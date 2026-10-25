"""IDL-1, the identity lever's experiment (experiments/idl1_identity_lever.py): the weight each reply puts on
the other firm, the readback that supplies the other firm's output for it, and the report.

The weight assumes the reply takes the other firm's output as given, so the report computes it only where
holding back can't pay for itself: against the fixed rival (its 24) and on the single-quarter start (the
readback's expected output), with no future and no mirror. On a repeated or mirrored start a cooperative 30
that expects 30 would score w = 1 with no sympathy at all, so those cells show counts and the replies' reasons
instead. Each identity's weight is also read as its gap from the same party's holding-company arm.

    uv run python experiments/idl1_identity_lever.py --models haiku sonnet opus   # run, then report
    uv run python -m zerocommcartel.criteria.communal.idl1 --models haiku sonnet opus   # the readbacks
"""

import argparse
import re
import statistics
from collections.abc import Callable
from pathlib import Path

from zerocommcartel import cli, logs
from zerocommcartel.call import MODELS, complete
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.communal.identity import CELLS, CITES, CONTROLS, DUOPOLY, FIRM_ARMS, FIXED
from zerocommcartel.criteria.conceptualization import readback
from zerocommcartel.criterion import Registry
from zerocommcartel.table import Replies, at_focal, fmt, markdown, model_rank

FOLDER = "communal/idl1"  # IDL-1's folder in logs/, from its id
WEIGHED = ("single", "fixed", "run")  # where holding back can't pay for itself
DUOPOLY_CELLS = tuple(name for name, (start, _, _) in CELLS.items() if start not in ("fixed", "run"))
FUTURE = re.compile(
    r"future|next quarter|later quarters|coming quarters|long[- ]run|repeat|retaliat|punish|trigger|"
    r"tit[- ]for[- ]tat|reputation",
    re.IGNORECASE,
)
NEGATED = re.compile(r"\b(?:no|not|never|without|nothing)\b|n't", re.IGNORECASE)  # "no future quarters"
HEADER = ["model", "cell", "replies", "invalid", "mean", "Nash", "cartel", "other", "expects", "w", "control",
          "Δ mean", "Δ w", "cites identity", "cites future"]  # fmt: skip


def weight(answer: float, rival: float, margin: float = 120) -> float | None:
    """The weight w on the other firm's profit that makes `answer` my firm's best response to the other firm
    at `rival`: the first-order condition margin - 2q - r - wr = 0. It takes the rival's output as given, so
    it means sympathy only where holding back can't pay for itself (against the fixed rival, or with no
    future and no mirror); elsewhere a cooperative 30 that expects 30 scores w = 1. None for a rival at 0 or
    below."""
    if rival <= 0:
        return None
    return (margin - 2 * answer - rival) / rival


def weights(name: str, rows: list[dict], readbacks: dict, registry: Registry) -> list[float] | None:
    """The weights of a cell's replies, or None where the cell isn't weighed: a bare cell or a firm identity
    where holding back can't pay for itself. A buyer's weight would read as spite toward the other firm."""
    start, identity, _ = CELLS[name]
    if start not in WEIGHED or identity not in (None, *FIRM_ARMS):
        return None
    margin = DUOPOLY.a - DUOPOLY.c  # every identity cell's market
    found = []
    for row in rows:
        if row["value"] is None:
            continue
        if start == "single":
            back = readback.lookup(readbacks, registry, "communal", row)
            rival = back.other if back else None
        else:
            rival = FIXED.rival  # the run-the-firm market's rival is the fixed one's
        if rival is not None and (w := weight(row["value"], rival, margin)) is not None:
            found.append(w)
    return found


def control_of(name: str) -> str | None:
    """The cell an identity is read against: its control arm from the same start point, on the plain
    question."""
    start, identity, ask = CELLS[name]
    control = f"id_{start}_{CONTROLS.get(identity or '')}"
    return control if ask == "plain" and control in CELLS else None


def cites_future(reply: str | None) -> bool:
    """Whether the reply speaks of the future, other than to say there is none ("no future quarters")."""
    text = reply or ""
    return any(not NEGATED.search(text[max(0, m.start() - 25) : m.start()]) for m in FUTURE.finditer(text))


def report(replies: Replies, readbacks: dict | None = None, registry: Registry = REGISTRY) -> str:
    """Per model and cell: replies and invalid answers, the mean answer, counts at Nash, at the cartel share
    and at the cell's other focal points, the median output the readbacks expected of the other firm, the
    median weight on the other firm where it's weighed, the gaps in mean answer and weight from the cell's
    control arm, and how many replies cite the cell's identity or the future. Then the failed calls."""
    if readbacks is None:
        readbacks = readback.load(readback.cache_path(logs.experiment_log(FOLDER)))
    cells: dict[tuple[str, str], list[dict]] = {}
    for row in replies.rows:
        if row["condition"] in CELLS:
            cells.setdefault((row["model"], row["condition"]), []).append(row)
    means, medians, expected = {}, {}, {}
    for key, rows in cells.items():
        if values := [r["value"] for r in rows if r["value"] is not None]:
            means[key] = statistics.mean(values)
        if found := weights(key[1], rows, readbacks, registry):
            medians[key] = (statistics.median(found), len(found))
        backs = [
            b.other
            for r in rows
            if (b := readback.lookup(readbacks, registry, "communal", r)) and b.other is not None
        ]
        if backs:
            expected[key] = (statistics.median(backs), len(backs))

    def gap(found: dict, key: tuple[str, str], control: str | None, form: str) -> str:
        theirs = (key[0], control)
        if not control or key not in found or theirs not in found:
            return "-"
        mine, other = (found[k][0] if isinstance(found[k], tuple) else found[k] for k in (key, theirs))
        return format(mine - other, form)

    order = {name: i for i, name in enumerate(CELLS)}
    lines = []
    for key in sorted(cells, key=lambda key: (model_rank(key[0]), order[key[1]])):
        model, name = key
        rows = cells[key]
        others = [focal for focal in rows[0]["focal"] if focal not in ("nash", "cartel")]
        control = control_of(name)
        pattern = CITES.get(CELLS[name][1] or "")
        lines.append(
            [
                model,
                name,
                str(len(rows)),
                str(sum(r["value"] is None for r in rows)),
                fmt(means[key]) if key in means else "-",
                str(sum(at_focal(r, "nash") for r in rows)),
                str(sum(at_focal(r, "cartel") for r in rows)),
                ", ".join(f"{focal} {sum(at_focal(r, focal) for r in rows)}" for focal in others),
                f"{expected[key][0]:g} ({expected[key][1]})" if key in expected else "-",
                f"{medians[key][0]:.2f} ({medians[key][1]})" if key in medians else "-",
                CELLS[control][1] if control else "-",
                gap(means, key, control, "+.1f"),
                gap(medians, key, control, "+.2f"),
                str(sum(bool(re.search(pattern, r["reply"] or "", re.IGNORECASE)) for r in rows))
                if pattern
                else "-",
                str(sum(cites_future(r["reply"]) for r in rows)),
            ]
        )
    failed = f"\n{replies.failed} call{'' if replies.failed == 1 else 's'} failed with no reply yet.\n"
    return markdown(HEADER, lines) + (failed if replies.failed else "")


def main(argv=None, registry: Registry = REGISTRY, call: Callable = complete):
    p = argparse.ArgumentParser(
        description="Ask each of IDL-1's duopoly replies what it expected the other firm to produce."
    )
    p.add_argument("--log", help=f"default: IDL-1's own, logs/{FOLDER}/results.jsonl")
    p.add_argument("--models", nargs="+", choices=list(MODELS))
    args = p.parse_args(argv)
    log = Path(args.log) if args.log else logs.experiment_log(FOLDER)
    rows = cli.replies(registry, "communal", str(log), list(DUOPOLY_CELLS), args.models).rows
    cache = readback.cache_path(log)
    asked, failed, cached = readback.ask(rows, registry, "communal", cache, call)
    print(f"readback: asked {asked}, {len(failed)} failed, {cached} already cached, into {cache}")
    for line in failed:
        print(f"  failed {line}")


if __name__ == "__main__":
    main()
