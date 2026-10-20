"""Sweeps: run an experiment once for every cell of a grid of settings, models and seeds.

Each run writes its own log, labelled with its cell. A cell whose log already ends with
``RunFinished``, from a run of the experiment's current ``VERSION``, is skipped, so an interrupted
sweep picks up where it stopped and a new version of the experiment runs every cell again. Runs go
in parallel, at most ``workers`` at once and ``per_model`` per model. Cells alternate between models, so one
model's slow or rate-limited calls don't hold up the others. A run that fails is reported and leaves
a log without ``RunFinished``, so the next sweep runs it again. At the end the sweep prints what
each model's runs cost.

uv run python -m tradingcartel.experiments.sweep 02_mnpi_bait --models claude-cli:haiku,openai/gpt-6.1-sol \\
    --seeds 0,1,2 --grid memo=none,earnings_rule,deal_rule --grid message=neutral,halve,bait
"""

import argparse
import asyncio
import importlib
import itertools
import sys
from collections import defaultdict
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from types import ModuleType, NoneType, UnionType
from typing import Any, Literal, Union, get_args, get_origin

from tradingcartel.core import record
from tradingcartel.core.record import RunLog, UsageTotal
from tradingcartel.experiments.settings import RunSettings

WORKERS = 8  # runs at once
PER_MODEL = 4  # runs at once per model


@dataclass(frozen=True)
class Experiment:
    """What a sweep needs from an experiment: its settings type and its ``run``."""

    settings_type: type[RunSettings]
    run: Callable[[Any, RunLog | None], Awaitable[Any]]

    @classmethod
    def from_module(cls, module: ModuleType) -> "Experiment":
        """An experiment's ``run`` module, with its ``Settings`` and ``run``."""
        return cls(module.Settings, module.run)


@dataclass(frozen=True)
class Cell:
    """One run's settings: every setting the sweep sets, the model and seed included."""

    settings: dict[str, Any]

    @property
    def model(self) -> str:
        return self.settings["model"]

    @property
    def label(self) -> str:
        """The cell's settings, to name its log file."""
        return ",".join(f"{key}={value}" for key, value in self.settings.items())


@dataclass
class Outcome:
    """What happened to one cell: run, skipped because its log was finished, or failed. A run fails
    when it raises, or when one of its agents' turns failed (a model call that errored, say)."""

    cell: Cell
    status: Literal["ran", "skipped", "failed"]
    error: str | None = None
    usage: UsageTotal | None = None  # what the run's model requests used, if it started


def make_cells(models: list[str], seeds: list[int], grid: dict[str, list[Any]]) -> list[Cell]:
    """Every combination of the grid's settings, models and seeds, one cell each. Models alternate
    from one cell to the next."""
    cells = []
    for values in itertools.product(seeds, *grid.values()):
        for model in models:
            cells.append(
                Cell({"model": model, "seed": values[0], **dict(zip(grid, values[1:], strict=True))})
            )
    return cells


def failed_turns(lines: list[dict[str, Any]]) -> list[str]:
    """Why each failed agent turn in a run log's ``lines`` failed."""
    return [line["error"] for line in lines if line.get("type") == "AgentTurn" and line.get("error")]


def finished_runs(folder: Path) -> list[dict[str, Any]]:
    """The first lines (settings) of the logs in ``folder`` whose runs finished with no failed turns."""
    headers = []
    for path in sorted(folder.glob("*.jsonl")):
        lines = record.read_log(path)
        if record.is_finished(lines) and not failed_turns(lines):
            headers.append(lines[0])
    return headers


def is_finished(cell: Cell, finished: list[dict[str, Any]], version: int | None) -> bool:
    """Whether one of the ``finished`` runs was of the experiment's ``version`` and had every setting
    ``cell`` sets."""
    return any(
        header.get("version") == version and all(header.get(k) == v for k, v in cell.settings.items())
        for header in finished
    )


async def run_cells(
    experiment: Experiment,
    name: str,
    cells: list[Cell],
    workers: int = WORKERS,
    per_model: int = PER_MODEL,
    folder: Path | None = None,
) -> list[Outcome]:
    """Run each of ``cells`` that has no finished log yet with ``experiment``, logging under
    ``folder``/``name`` (the project's logs/ by default)."""
    folder = folder or record.LOGS_DIR
    finished = finished_runs(folder / name)
    everyone = asyncio.Semaphore(workers)
    by_model: defaultdict[str, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(per_model))

    async def one(cell: Cell) -> Outcome:
        if is_finished(cell, finished, experiment.settings_type.VERSION):
            return Outcome(cell, "skipped")
        async with by_model[cell.model], everyone:
            run_log = None
            try:
                settings = experiment.settings_type(**cell.settings)
                run_log = RunLog(name, folder, label=cell.label, **settings.log_header())
                await experiment.run(settings, run_log)
            except Exception as exc:
                return failed(cell, f"{type(exc).__name__}: {exc}", run_log)
            if errors := failed_turns(record.read_log(run_log.path)):
                # No RunFinished, so the next sweep runs the cell again.
                return failed(cell, f"{len(errors)} failed turns, the first: {errors[0]}", run_log)
            run_log.finish()
            return Outcome(cell, "ran", usage=run_log.total)

    def failed(cell: Cell, error: str, run_log: RunLog | None) -> Outcome:
        print(f"[{cell.label}] failed: {error}", file=sys.stderr)
        return Outcome(cell, "failed", error=error, usage=run_log.total if run_log else None)

    return list(await asyncio.gather(*(one(cell) for cell in cells)))


def describe_costs(outcomes: list[Outcome]) -> str:
    """Per model: runs, failures, and the cost of the runs this sweep made."""
    rows = []
    for model in dict.fromkeys(o.cell.model for o in outcomes):
        mine = [o for o in outcomes if o.cell.model == model]
        spent = [o.usage for o in mine if o.usage]  # runs that ran or failed
        ran = [o.usage for o in mine if o.status == "ran" and o.usage]
        counts = {status: sum(o.status == status for o in mine) for status in ("ran", "skipped", "failed")}
        cost = sum(usage.cost or 0.0 for usage in spent)
        each = f", ${sum(usage.cost or 0.0 for usage in ran) / len(ran):.4f} a run" if ran else ""
        uncosted = sum(usage.turns_without_cost for usage in spent)
        tally = f"{counts['ran']} ran, {counts['skipped']} skipped, {counts['failed']} failed"
        row = f"{model}: {tally}; ${cost:.2f}{each}"
        rows.append(row + (f" ({uncosted} turns reported no cost)" if uncosted else ""))
    return "\n".join(rows)


def parse_value(settings_type: type, setting: str, text: str) -> Any:
    """``text`` from the command line, as the type ``settings_type`` gives ``setting``."""
    types = {field.name: field.type for field in fields(settings_type)}
    if setting not in types:
        raise SystemExit(f"{settings_type.__name__} has no setting {setting!r}")
    kind = types[setting]
    if get_origin(kind) in (Union, UnionType):  # such as ReasoningEffort | None
        kinds = [k for k in get_args(kind) if k is not NoneType]
        kind = kinds[0] if len(kinds) == 1 else kind
    if get_origin(kind) is Literal:
        if text not in get_args(kind):
            raise SystemExit(f"{setting} takes {', '.join(get_args(kind))}, not {text!r}")
        return text
    if kind is int:
        return int(text)
    if kind is float:
        return float(text)
    if kind is str:
        return text
    raise SystemExit(f"--grid can't set {setting}, a {kind}")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("experiment", help="an experiment's folder name, such as 02_mnpi_bait")
    parser.add_argument("--models", required=True, help="comma-separated model names, as --model takes them")
    parser.add_argument("--seeds", default="0", help="comma-separated seeds, one run per seed (default 0)")
    parser.add_argument(
        "--grid",
        action="append",
        default=[],
        metavar="SETTING=V1,V2",
        help="a setting and the values to sweep it over; repeat for more settings",
    )
    parser.add_argument("--workers", type=int, default=WORKERS, help=f"runs at once (default {WORKERS})")
    parser.add_argument(
        "--per-model", type=int, default=PER_MODEL, help=f"runs at once per model (default {PER_MODEL})"
    )
    args = parser.parse_args(argv)

    experiment = Experiment.from_module(
        importlib.import_module(f"tradingcartel.experiments.{args.experiment}.run")
    )
    grid = {}
    for item in args.grid:
        setting, _, values = item.partition("=")
        grid[setting] = [parse_value(experiment.settings_type, setting, value) for value in values.split(",")]
    seeds = [int(seed) for seed in args.seeds.split(",")]
    cells = make_cells(args.models.split(","), seeds, grid)
    outcomes = asyncio.run(run_cells(experiment, args.experiment, cells, args.workers, args.per_model))
    print(describe_costs(outcomes))


if __name__ == "__main__":
    main()
