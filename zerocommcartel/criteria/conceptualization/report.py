"""The conceptualization report (#42): each model's replies as a ladder, one line per background.

The columns run down the ladder, from "this same AI model with this same prompt" to the rival that won't
cooperate; the lines are the twelve backgrounds. A cell counts the parsed answers at a focal point (the
cartel share unless --at names another) as "k/m": "-" when the cell has no parsed answer, "n/a" when the
focal point isn't one of that cell's. With the readback's cache beside the log, a second grid per model
counts the replies whose expected rival output equals their own answer ("expects a match"), of those with a
readback.

    uv run python -m zerocommcartel.criteria.conceptualization.report
    uv run python -m zerocommcartel.criteria.conceptualization.report --at "cash in" --models haiku
"""

import argparse
from collections import defaultdict
from collections.abc import Callable

from zerocommcartel import cli
from zerocommcartel.call import MODELS
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.conceptualization import (
    CRITERION,
    HORIZONS,
    RECORDS,
    RUNGS,
    final,
    name,
    readback,
)
from zerocommcartel.criterion import Registry, near
from zerocommcartel.table import markdown, model_rank

HORIZON_LABELS = {"unsaid": "no repeat mentioned", "single": "one quarter only", "open": "repeats"}
RECORD_LABELS = {"none": "", "coop": ", after 30s", "cheat": ", after a cheat", "nash": ", after 40s"}


def background(horizon: str, record: str) -> str:
    """A background's label; a single quarter after a record is the market's final one."""
    if final(horizon, record):
        return "final quarter" + RECORD_LABELS[record]
    return HORIZON_LABELS[horizon] + RECORD_LABELS[record]


def grid(cell: Callable[[str], str]) -> str:
    """A line per background and a column per rung; `cell` gives a condition's cell."""
    lines = [
        [background(horizon, record), *(cell(name(rung, horizon, record)) for rung in RUNGS)]
        for horizon in HORIZONS
        for record in RECORDS
    ]
    return markdown(["background", *RUNGS], lines)


def parsed(rows: list[dict], model: str) -> dict[str, list[dict]]:
    """The model's rows with a number, by condition."""
    cells: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["model"] == model and row["value"] is not None:
            cells[row["condition"]].append(row)
    return cells


def ladder(rows: list[dict], model: str, at: str = "cartel") -> str:
    cells = parsed(rows, model)

    def cell(condition: str) -> str:
        found = cells.get(condition)
        if not found:
            return "-"
        target = found[0]["focal"].get(at)
        if target is None:
            return "n/a"
        return f"{sum(near(row['value'], target) for row in found)}/{len(found)}"

    return grid(cell)


def matches(rows: list[dict], model: str, readbacks: dict[str, readback.Readback], registry: Registry) -> str:
    cells = parsed(rows, model)

    def prompt_of(row: dict):
        return readback.prompt_of(registry, CRITERION.name, row)

    def cell(condition: str) -> str:
        expected = [
            (row["value"], got.other)
            for row in cells.get(condition, [])
            if (got := readbacks.get(readback.key(model, prompt_of(row), row["sample"], row["reply"])))
            and got.other is not None
        ]
        if not expected:
            return "-"
        return f"{sum(near(value, other) for value, other in expected)}/{len(expected)}"

    return grid(cell)


def main(argv=None, registry: Registry = REGISTRY):
    p = argparse.ArgumentParser(description="Each model's replies as a ladder, one line per background.")
    p.add_argument("--log", help=cli.LOG_HELP)
    p.add_argument("--at", default="cartel", help="the focal point the cells count (default: cartel)")
    p.add_argument("--models", nargs="+", choices=list(MODELS))
    args = p.parse_args(argv)
    conditions = list(CRITERION.conditions)
    rows = cli.replies(registry, CRITERION.name, args.log, conditions, args.models).rows
    readbacks = readback.load(readback.cache_path(cli.sources(registry, CRITERION.name, args.log).log))
    for model in sorted({row["model"] for row in rows}, key=model_rank):
        print(f"## {model}: answers at {args.at}\n\n{ladder(rows, model, args.at)}")
        if readbacks:
            print(f"### {model}: replies that expect a match\n\n{matches(rows, model, readbacks, registry)}")


if __name__ == "__main__":
    main()
