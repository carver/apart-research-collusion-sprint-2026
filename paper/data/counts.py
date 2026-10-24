"""Counting a criterion's replies for the paper: parsed answers at a focal point, one cell's or pooled.

The rows are a criterion's `zerocommcartel.table.Replies` rows, so the paper counts what `zcc table` counts:
the last reply per call to each condition's current wording, read with today's parser, with its cell's focal
points and its judges' labels. A count's denominator is the parsed answers. This module has no source."""

from collections.abc import Callable, Collection

from paper.ledger import CELL, Ledger, display
from zerocommcartel.criterion import NEAR, near

# the five models every criterion runs, by their names in the tables
STANDARD = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus", "astra": "Astra", "glm": "GLM"}


def at(focal: str) -> Callable[[dict], bool]:
    """An answer within NEAR of its cell's focal point `focal`, as zcc counts it."""
    return lambda row: near(row["value"], row["focal"][focal])


def below(focal: str) -> Callable[[dict], bool]:
    """An answer more than NEAR below its cell's focal point `focal`."""
    return lambda row: row["value"] < row["focal"][focal] - NEAR


def chosen(
    rows: list[dict],
    conditions: Collection[str],
    ns: Collection[int] | None = None,
    models: Collection[str] | None = STANDARD,
) -> list[dict]:
    """The rows of `conditions` with a parsed answer, at the market sizes `ns` and from `models`; every size
    or model when that is None."""
    return [
        row
        for row in rows
        if row["condition"] in conditions
        and row["value"] is not None
        and (ns is None or row["n"] in ns)
        and (models is None or row["model"] in models)
    ]


def count(ledger: Ledger, key: str, rows: list[dict], hit: Callable[[dict], bool], how: str) -> None:
    """Records how many `rows` are a `hit`: one cell's as a rate with its interval, several cells' pooled."""
    if len({tuple(row[field] for field in CELL) for row in rows}) == 1:
        ledger.rate(key, rows, hit, how)
    else:
        ledger.pooled(key, rows, hit, how)


def line(
    ledger: Ledger,
    label: str,
    stem: str,
    suffix: str,
    rows: list[dict],
    hit: Callable[[dict], bool],
    how: str,
) -> list[str]:
    """A table line: `label`, then the hits of each standard model's rows and of all five, as k/n. Records
    each count under <stem>.<model>.<suffix> and the five's under <stem>.<suffix>; a model with no rows, or
    all five, shows "-" and records nothing."""

    def cell(key: str, found: list[dict], how: str) -> str:
        if not found:
            return "-"
        count(ledger, key, found, hit, how)
        return display(ledger.entries[key])

    by_model = [cell(f"{stem}.{m}.{suffix}", [r for r in rows if r["model"] == m], how) for m in STANDARD]
    five = [row for row in rows if row["model"] in STANDARD]
    return [label, *by_model, cell(f"{stem}.{suffix}", five, f"{how}; the five standard models")]
