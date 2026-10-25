"""Which of IDL-1's cells a model still needs fresh replies in (#41), for both of its two-stage tests: Figure
1's gate (`idl1.verdicts`) and the cross-model appendix (`crossmodel.verdicts`). It needs no refusal labels,
so whoever runs a model's calls can find its cells before the judge runs.

    uv run python -m zerocommcartel.criteria.communal.fresh astra           # the cells, for --conditions
    uv run python -m zerocommcartel.criteria.communal.fresh astra --check   # complete yet? exits 1 if not
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

from zerocommcartel import cli, logs
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.communal.crossmodel import first_stage, screened, start_of
from zerocommcartel.criteria.communal.identity import CELLS
from zerocommcartel.criteria.communal.idl1 import DUOPOLY_CELLS, FIRST, FOLDER, Unlabelled, counted, verdicts
from zerocommcartel.criteria.communal.judge import REFUSAL, at_cartel
from zerocommcartel.criteria.conceptualization import readback
from zerocommcartel.judge import load_labels

FRESH = 30  # fresh replies a model in a cell tested again


def cells(rows: list[dict], model: str, labels: dict[str, dict] | None = None) -> list[str]:
    """The cells where `model` needs fresh replies: the target and reference of each of its tests that went
    to Figure 1's fresh stage, and every cell passing the cross-model test's first stage with its
    nothing-said start; in `DUOPOLY_CELLS` order. With refusal labels that first stage is the test's own
    (`crossmodel.first_stage`, raising Unlabelled where they fall short); without, it is the share test alone
    (`crossmodel.screened`), a superset. Raises ValueError when the model's first stage is incomplete."""
    if model not in counted(rows)[1]:
        raise ValueError(f"{model}: IDL-1's first stage isn't complete ({FIRST} replies in every cell)")
    pending = {
        cell
        for c in verdicts(rows)
        if c.model == model and c.stage != "first"
        for cell in (c.target, c.reference)
    }
    if labels is None:
        screen = set(screened(rows))
    else:
        screen = {v.cell for v in first_stage(rows, labels) if v.passes}
    wanted = pending | screen | {start for cell in screen if (start := start_of(cell))}
    return [cell for cell in DUOPOLY_CELLS if cell in wanted]


def duopoly(rows: list[dict], model: str) -> list[dict]:
    """The model's replies in IDL-1's duopoly cells."""
    return [row for row in rows if row["model"] == model and row["condition"] in DUOPOLY_CELLS]


def missing(rows: list[dict], model: str, needed: list[str]) -> int:
    """The fresh replies `needed` cells still lack for `model`, against FRESH a cell."""
    have = Counter(row["condition"] for row in duopoly(rows, model) if row["sample"] >= FIRST)
    return sum(max(FRESH - have[cell], 0) for cell in needed)


def unlabelled(rows: list[dict], model: str, labels: dict[str, dict]) -> int:
    """The model's duopoly replies off the cartel share that the refusal judge hasn't labelled; the paper's
    build stops on them."""
    return sum(not at_cartel(row) and REFUSAL.key(row["reply"]) not in labels for row in duopoly(rows, model))


def unread(rows: list[dict], model: str, readbacks: dict) -> int:
    """The model's first-stage duopoly replies with no readback cached. The paper doesn't read them, so a
    few left over can be asked later on any Codex login."""
    return sum(
        row["sample"] < FIRST and readback.lookup(readbacks, REGISTRY, "communal", row) is None
        for row in duopoly(rows, model)
    )


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="The IDL-1 cells where a model still needs fresh replies.")
    p.add_argument("model")
    p.add_argument("--check", action="store_true", help="say whether they're complete; exit 1 if not")
    p.add_argument("--log", help=f"default: IDL-1's own, logs/{FOLDER}/results.jsonl")
    args = p.parse_args(argv)
    log = Path(args.log) if args.log else logs.experiment_log(FOLDER)
    rows = cli.replies(REGISTRY, "communal", str(log), list(CELLS), None).rows
    labels = load_labels(REFUSAL, logs.judge_path(log, REFUSAL.name))
    try:
        needed = cells(rows, args.model, labels)
    except Unlabelled:
        print("refusal labels incomplete: listing the cells the share test alone passes", file=sys.stderr)
        needed = cells(rows, args.model)
    except ValueError as e:
        sys.exit(str(e))
    if not args.check:
        print(" ".join(needed))
        return
    left, unjudged = missing(rows, args.model, needed), unlabelled(rows, args.model, labels)
    if left or unjudged:
        print(
            f"{args.model}: {left} fresh replies still missing in IDL-1's cells, and {unjudged} replies "
            "without a refusal label; run it again"
        )
        sys.exit(1)
    note = f"{args.model}: IDL-1's fresh replies and refusal labels are complete, in its {len(needed)} cells"
    if waiting := unread(rows, args.model, readback.load(readback.cache_path(log))):
        note += f"; {waiting} first-stage replies have no readback (not needed for the paper)"
    print(note)


if __name__ == "__main__":
    main()
