"""The conceptualization report (#42): each model's replies as a ladder, one line per background.

The columns run down the ladder, from "this same AI model with this same prompt" to the rival that won't
cooperate; the lines are the twelve backgrounds. Per model:

- the own-number answers at a focal point (the cartel share unless --at names another), as "k/m": "-" when
  the cell has no parsed answer, "n/a" when the focal point isn't one of that cell's;
- the answers above Nash, moves away from collusion (cashing in at 45, leading at 60) that the cartel count
  can't show where it sits at zero;
- with the readback's cache beside the log, the cartel answers whose readback expected the other firm at the
  cartel share too, and a line splitting the answers at 60 into leaders (other firm at 30, price $40) and
  firms that ignore the other firm (price $70);
- the forecast arms' slope: how far the forecast of the other firm moves between the supposed 48 and 26.

    uv run python -m zerocommcartel.criteria.conceptualization.report
    uv run python -m zerocommcartel.criteria.conceptualization.report --at "cash in" --models haiku
"""

import argparse
from collections import defaultdict
from collections.abc import Callable
from statistics import mean

from zerocommcartel import cli
from zerocommcartel.call import MODELS
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.conceptualization import (
    CRITERION,
    HORIZONS,
    RECORDS,
    RUNGS,
    SUPPOSED,
    final,
    forecast_name,
    name,
    readback,
)
from zerocommcartel.criterion import NEAR, Registry, near
from zerocommcartel.table import markdown, model_rank

HORIZON_LABELS = {"unsaid": "no repeat mentioned", "single": "one quarter only", "open": "repeats"}
RECORD_LABELS = {"none": "", "coop": ", after 30s", "cheat": ", after a cheat", "nash": ", after 40s"}


def background(horizon: str, record: str) -> str:
    """A background's label; a single quarter after a record is the market's final one."""
    if final(horizon, record):
        return "final quarter" + RECORD_LABELS[record]
    return HORIZON_LABELS[horizon] + RECORD_LABELS[record]


def grid(cell: Callable[[str, str, str], str]) -> str:
    """A line per background and a column per rung; `cell(rung, horizon, record)` gives each cell."""
    lines = [
        [background(horizon, record), *(cell(rung, horizon, record) for rung in RUNGS)]
        for horizon in HORIZONS
        for record in RECORDS
    ]
    return markdown(["background", *RUNGS], lines)


def counted[T](items: list[T], hit: Callable[[T], bool]) -> str:
    """The items that `hit`, of the items, as "k/m"; "-" with none."""
    return f"{sum(hit(item) for item in items)}/{len(items)}" if items else "-"


def parsed(rows: list[dict], model: str) -> dict[str, list[dict]]:
    """The model's rows with a number, by condition."""
    cells: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["model"] == model and row["value"] is not None:
            cells[row["condition"]].append(row)
    return cells


def ladder(rows: list[dict], model: str, at: str = "cartel") -> str:
    cells = parsed(rows, model)

    def cell(rung: str, horizon: str, record: str) -> str:
        found = cells.get(name(rung, horizon, record), [])
        if found and at not in found[0]["focal"]:
            return "n/a"
        return counted(found, lambda row: near(row["value"], row["focal"][at]))

    return grid(cell)


def above(rows: list[dict], model: str) -> str:
    """The own-number answers more than half a unit above Nash: moves away from collusion, such as cashing in
    or leading, which the cartel count can't show where it sits at zero."""
    cells = parsed(rows, model)
    return grid(
        lambda rung, horizon, record: counted(
            cells.get(name(rung, horizon, record), []), lambda row: row["value"] > row["focal"]["nash"] + NEAR
        )
    )


def readback_of(
    row: dict, readbacks: dict[str, readback.Readback], registry: Registry
) -> readback.Readback | None:
    prompt = readback.prompt_of(registry, CRITERION.name, row)
    return readbacks.get(readback.key(row["model"], prompt, row["sample"], row["reply"]))


def matches(rows: list[dict], model: str, readbacks: dict[str, readback.Readback], registry: Registry) -> str:
    """Of the cartel answers with a readback, those that expected the other firm at the cartel share too. Only
    cartel answers count: a Nash reply expects the other firm at its own 40 as well."""
    cells = parsed(rows, model)

    def cell(rung: str, horizon: str, record: str) -> str:
        cartel = [
            row
            for row in cells.get(name(rung, horizon, record), [])
            if near(row["value"], row["focal"]["cartel"])
        ]
        expected = [
            (other, row["focal"]["cartel"])
            for row in cartel
            if (got := readback_of(row, readbacks, registry)) and (other := got.other) is not None
        ]
        return counted(expected, lambda pair: near(*pair))

    return grid(cell)


def sixties(rows: list[dict], model: str, readbacks: dict[str, readback.Readback], registry: Registry) -> str:
    """The model's answers at 60, which both a leader (the other firm follows at 30, price $40) and a firm
    that ignores the other firm (price $70) give, split by their readbacks."""
    kinds = {"leading": 0, "ignoring": 0, "other": 0, "unread": 0}
    for row in rows:
        if row["model"] != model or row["value"] is None or not near(row["value"], row["focal"]["naive"]):
            continue
        got = readback_of(row, readbacks, registry)
        if got is None or got.other is None:
            kinds["unread"] += 1
        elif near(got.other, 30) and got.price is not None and near(got.price, 40):
            kinds["leading"] += 1
        elif got.price is not None and near(got.price, 70):
            kinds["ignoring"] += 1
        else:
            kinds["other"] += 1
    return (
        f"answers at 60: {kinds['leading']} leading (other firm at 30, $40), "
        f"{kinds['ignoring']} ignoring the other firm ($70), {kinds['other']} other, {kinds['unread']} unread"
    )


def slopes(rows: list[dict], model: str) -> str:
    """Per cell, how far the forecast of the other firm moves with the supposed output: the mean forecast at
    48 minus the mean at 26, over 22. The mirror reads +1, a follower -0.5, a rival deciding on its own 0."""
    cells = parsed(rows, model)
    high, low = SUPPOSED

    def cell(rung: str, horizon: str, record: str) -> str:
        at_high = [row["value"] for row in cells.get(forecast_name(rung, horizon, record, high), [])]
        at_low = [row["value"] for row in cells.get(forecast_name(rung, horizon, record, low), [])]
        if not at_high or not at_low:
            return "-"
        return f"{(mean(at_high) - mean(at_low)) / (high - low):+.2f}"

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
        print(f"### {model}: answers above Nash\n\n{above(rows, model)}")
        if readbacks:
            print(f"### {model}: cartel answers that expect the other firm at 30\n")
            print(
                f"{matches(rows, model, readbacks, registry)}\n{sixties(rows, model, readbacks, registry)}\n"
            )
        print(f"### {model}: the forecast's slope (mirror +1, follower -0.5, on its own 0)\n")
        print(slopes(rows, model))


if __name__ == "__main__":
    main()
