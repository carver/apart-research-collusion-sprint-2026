"""Sweeps: run an experiment once for every cell of a grid of settings, models and seeds.

Each run writes its own log, labelled with its cell. A cell whose log already ends with
``RunFinished`` is skipped, so an interrupted sweep picks up where it stopped. Runs go in parallel,
at most ``workers`` at once and ``per_model`` per model. Cells alternate between models, so one
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
import json
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from types import ModuleType
from typing import Any, Literal, get_args, get_origin

from tradingcartel.core import record
from tradingcartel.core.record import RunLog


@dataclass(frozen=True)
class Cell:
    """One run's settings: every setting the sweep sets, the model and seed included."""

    settings: dict[str, Any]

    @property
    def label(self) -> str:
        """The cell's settings, as a name for its log file."""
        return record.safe_name(",".join(f"{key}={value}" for key, value in self.settings.items()))


@dataclass
class Outcome:
    """What happened to one cell: run, skipped because its log was finished, or failed."""

    cell: Cell
    status: Literal["ran", "skipped", "failed"]
    error: str | None = None
    totals: dict[str, Any] | None = None  # the run's RunFinished totals, if it ran


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


def finished_runs(folder: Path) -> list[dict[str, Any]]:
    """The first lines (settings) of the logs in ``folder`` that end with ``RunFinished``."""
    headers = []
    for path in sorted(folder.glob("*.jsonl")):
        lines = path.read_text().splitlines()
        if lines and json.loads(lines[-1]).get("type") == "RunFinished":
            headers.append(json.loads(lines[0]))
    return headers


def is_finished(cell: Cell, finished: list[dict[str, Any]]) -> bool:
    """Whether one of the ``finished`` runs had every setting ``cell`` sets."""
    return any(all(header.get(k) == v for k, v in cell.settings.items()) for header in finished)


async def run_cells(
    experiment: ModuleType,
    name: str,
    cells: list[Cell],
    workers: int = 8,
    per_model: int = 4,
    folder: Path | None = None,
) -> list[Outcome]:
    """Run each of ``cells`` that has no finished log yet with ``experiment``'s ``Settings`` and
    ``run``, logging under ``folder``/``name`` (the project's logs/ by default)."""
    folder = folder or record.LOGS_DIR
    finished = finished_runs(folder / name)
    everyone = asyncio.Semaphore(workers)
    by_model: defaultdict[str, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(per_model))

    async def one(cell: Cell) -> Outcome:
        if is_finished(cell, finished):
            return Outcome(cell, "skipped")
        async with by_model[cell.settings["model"]], everyone:
            settings = experiment.Settings(**cell.settings)
            run_log = RunLog(name, folder, label=cell.label, **settings.log_header())
            try:
                await experiment.run(settings, run_log)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                print(f"[{cell.label}] failed: {error}", file=sys.stderr)
                return Outcome(cell, "failed", error=error)
            return Outcome(cell, "ran", totals=run_log.finish())

    return list(await asyncio.gather(*(one(cell) for cell in cells)))


def describe_costs(outcomes: list[Outcome]) -> str:
    """Per model: runs, failures, and the cost of the runs this sweep made."""
    rows = []
    for model in dict.fromkeys(o.cell.settings["model"] for o in outcomes):
        mine = [o for o in outcomes if o.cell.settings["model"] == model]
        ran = [o.totals["total"] for o in mine if o.status == "ran" and o.totals]
        counts = {status: sum(o.status == status for o in mine) for status in ("ran", "skipped", "failed")}
        cost = sum(total["cost"] or 0.0 for total in ran)
        each = f", ${cost / len(ran):.4f} a run" if ran else ""
        uncosted = sum(total["turns_without_cost"] for total in ran)
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
    if get_origin(kind) is Literal:
        if text not in get_args(kind):
            raise SystemExit(f"{setting} takes {', '.join(get_args(kind))}, not {text!r}")
        return text
    if kind is int:
        return int(text)
    if kind is float:
        return float(text)
    return text


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
    parser.add_argument("--workers", type=int, default=8, help="runs at once (default 8)")
    parser.add_argument("--per-model", type=int, default=4, help="runs at once per model (default 4)")
    args = parser.parse_args(argv)

    experiment = importlib.import_module(f"tradingcartel.experiments.{args.experiment}.run")
    grid = {}
    for item in args.grid:
        setting, _, values = item.partition("=")
        grid[setting] = [parse_value(experiment.Settings, setting, value) for value in values.split(",")]
    seeds = [int(seed) for seed in args.seeds.split(",")]
    cells = make_cells(args.models.split(","), seeds, grid)
    outcomes = asyncio.run(run_cells(experiment, args.experiment, cells, args.workers, args.per_model))
    print(describe_costs(outcomes))


if __name__ == "__main__":
    main()
