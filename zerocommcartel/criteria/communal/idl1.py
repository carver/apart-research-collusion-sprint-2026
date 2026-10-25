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
import math
import re
import statistics
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

from zerocommcartel import cli, logs
from zerocommcartel.call import MODELS, complete
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.communal.games import FixedRival
from zerocommcartel.criteria.communal.identity import CELLS, CITES, CONTROLS, DUOPOLY, FIRM_ARMS, STARTS
from zerocommcartel.criteria.conceptualization import readback
from zerocommcartel.criterion import Registry, near
from zerocommcartel.table import Replies, at_focal, fmt, markdown, model_rank

FOLDER = "communal/idl1"  # IDL-1's folder in logs/, from its id
DUOPOLY_CELLS = tuple(name for name, cell in CELLS.items() if not isinstance(cell.game, FixedRival))
FUTURE = re.compile(
    r"future|next quarter|later quarters|coming quarters|long[- ]run|repeat|retaliat|punish|trigger|"
    r"tit[- ]for[- ]tat|reputation",
    re.IGNORECASE,
)
NEGATED = re.compile(r"\b(?:no|not|never|without|nothing)\b|n't", re.IGNORECASE)  # "no future quarters"
HEADER = ["model", "cell", "replies", "invalid", "mean", "Nash", "cartel", "other", "expects", "w", "control",
          "Δ mean", "Δ w", "cites identity", "cites future"]  # fmt: skip


def weight(answer: float, rival: float, margin: float = DUOPOLY.a - DUOPOLY.c) -> float | None:
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
    where holding back can't pay for itself, against the fixed rival (its output is the game's) or in the
    single quarter (the readback's). A buyer's weight would read as spite toward the other firm."""
    cell = CELLS[name]
    game = cell.game
    if cell.identity not in (None, *FIRM_ARMS) or not (
        isinstance(game, FixedRival) or cell.start == "single"
    ):
        return None
    found = []
    for row in rows:
        if row["value"] is None:
            continue
        if isinstance(game, FixedRival):
            rival = game.rival
        else:
            back = readback.lookup(readbacks, registry, "communal", row)
            rival = back.other if back else None
        if rival is not None and (w := weight(row["value"], rival, game.a - game.c)) is not None:
            found.append(w)
    return found


def control_of(name: str) -> str | None:
    """The cell an identity is read against: its control arm from the same start point, on the plain
    question."""
    cell = CELLS[name]
    control = f"id_{cell.start}_{CONTROLS.get(cell.identity or '')}"
    return control if cell.ask == "plain" and control in CELLS else None


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
    means: dict[tuple[str, str], float] = {}
    weighed: dict[tuple[str, str], list[float]] = {}
    expected: dict[tuple[str, str], list[float]] = {}  # the other firm's output, as the readbacks expected it
    for key, rows in cells.items():
        if values := [r["value"] for r in rows if r["value"] is not None]:
            means[key] = statistics.mean(values)
        if found := weights(key[1], rows, readbacks, registry):
            weighed[key] = found
        backs = [readback.lookup(readbacks, registry, "communal", r) for r in rows]
        if others := [b.other for b in backs if b and b.other is not None]:
            expected[key] = others
    medians = {key: statistics.median(found) for key, found in weighed.items()}

    def median_of(found: dict[tuple[str, str], list[float]], key: tuple[str, str], form: str) -> str:
        return f"{statistics.median(found[key]):{form}} ({len(found[key])})" if key in found else "-"

    def gap(found: dict[tuple[str, str], float], key: tuple[str, str], control: str | None, form: str) -> str:
        if control is None or key not in found or (key[0], control) not in found:
            return "-"
        return format(found[key] - found[(key[0], control)], form)

    order = {name: i for i, name in enumerate(CELLS)}
    lines = []
    for key in sorted(cells, key=lambda key: (model_rank(key[0]), order[key[1]])):
        model, name = key
        rows = cells[key]
        others = [focal for focal in rows[0]["focal"] if focal not in ("nash", "cartel")]
        control = control_of(name)
        pattern = CITES.get(CELLS[name].identity or "")
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
                median_of(expected, key, "g"),
                median_of(weighed, key, ".2f"),
                CELLS[control].identity if control else "-",
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


def fisher(hits: int, n: int, other_hits: int, other_n: int) -> float:
    """Fisher's exact test, two-sided, of hits/n against other_hits/other_n: the chance, with the margins
    fixed, of a table no likelier than this one. Integer weights, so ties count exactly."""
    both, total = hits + other_hits, n + other_n

    def weight(x: int) -> int:
        return math.comb(both, x) * math.comb(total - both, n - x)

    observed = weight(hits)
    tables = range(max(0, n - (total - both)), min(both, n) + 1)
    return sum(w for x in tables if (w := weight(x)) <= observed) / math.comb(total, n)


def benjamini_hochberg(ps: list[float]) -> list[float]:
    """Benjamini-Hochberg q-values, in the order of `ps`: each p times m over its rank, then the running
    minimum from the largest p down, capped at 1."""
    m = len(ps)
    qs, running = [1.0] * m, 1.0
    for rank, i in reversed(list(enumerate(sorted(range(m), key=lambda i: ps[i]), 1))):
        running = min(running, ps[i] * m / rank)
        qs[i] = running
    return qs


def wilson_share(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """The Wilson score interval for hits/n, as shares."""
    p, z2 = hits / n, z * z
    centre, half = (
        (p + z2 / (2 * n)) / (1 + z2 / n),
        z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n),
    )
    return centre - half, centre + half


def newcombe(hits: int, n: int, other_hits: int, other_n: int, z: float = 1.96) -> tuple[float, float]:
    """Newcombe's hybrid score interval (his method 10) for hits/n minus other_hits/other_n, from the two
    Wilson intervals."""
    p1, p2 = hits / n, other_hits / other_n
    (l1, u1), (l2, u2) = wilson_share(hits, n, z), wilson_share(other_hits, other_n, z)
    d = p1 - p2
    return d - math.hypot(p1 - l1, u2 - p2), d + math.hypot(u1 - p1, p2 - l2)


class Comparison(NamedTuple):
    model: str
    start: str
    target: str  # the cell under test
    reference: str  # its control, or the bare start
    stage: str  # "first", "fresh", or "unconfirmed"
    hits: int
    n: int
    reference_hits: int
    reference_n: int
    p: float
    q: float
    passes: bool


SCREEN = 3  # replies of 10 a comparison must move, short of passing, to earn a confirmation run
Q = 0.10  # Benjamini-Hochberg's bar
FIRST = 10  # samples 0-9 are the first stage; 10-39 the fresh replies of a confirmation run
SANITY = "both_holding"  # one owner over both firms: a sanity check, kept out of the family
DUOPOLY_STARTS = tuple(start for start in STARTS if start != "fixed")  # the count at 30 means collusion there


def counted(rows: list[dict]) -> tuple[dict, dict, list[str]]:
    """Replies at the cartel share and replies, by (model, cell, stage), and the models with every cell at its
    first stage's 10 replies."""
    hits: dict[tuple[str, str, str], int] = {}
    n: dict[tuple[str, str, str], int] = {}
    for row in rows:
        if row["condition"] not in CELLS:
            continue
        key = (row["model"], row["condition"], "first" if row["sample"] < FIRST else "fresh")
        n[key] = n.get(key, 0) + 1
        hits[key] = hits.get(key, 0) + (
            row["value"] is not None and near(row["value"], DUOPOLY.benchmarks(2)["cartel"])
        )
    models = sorted({m for m, _, _ in n}, key=model_rank)
    return hits, n, [m for m in models if all(n.get((m, name, "first"), 0) >= FIRST for name in CELLS)]


def family(models: list[str]) -> list[tuple[str, str, str, str]]:
    """The tests, as (model, start, target, reference): each identity against its control from the same
    duopoly start, on the plain question, and each control against the bare start, one owner over both firms
    aside."""
    found = []
    for model in models:
        for name, cell in CELLS.items():
            control = CONTROLS.get(cell.identity or "")
            if control and cell.ask == "plain" and cell.start in DUOPOLY_STARTS:
                found.append((model, cell.start, name, f"id_{cell.start}_{control}"))
        for start in DUOPOLY_STARTS:
            for control in sorted(set(CONTROLS.values()) - {SANITY}):
                if f"id_{start}_{control}" in CELLS:
                    found.append((model, start, f"id_{start}_{control}", f"id_{start}_base"))
    return found


def verdicts(rows: list[dict]) -> list[Comparison]:
    """Each test's verdict. First stage: Fisher's exact test on the first 10 replies a cell,
    Benjamini-Hochberg across the family, q < 0.10 passes. A test that moved 3 or more replies but missed is
    pending: tested again on its fresh replies only, Benjamini-Hochberg across the pending tests; one without
    fresh replies stays unconfirmed. The rule was fixed before the fresh replies ran (#41)."""
    hits, n, models = counted(rows)

    def get(cell: tuple[str, str], stage: str) -> tuple[int, int]:
        return hits.get((*cell, stage), 0), n.get((*cell, stage), 0)

    tests = family(models)
    first = [(*get((m, t), "first"), *get((m, r), "first")) for m, _, t, r in tests]
    ps = [fisher(*counts) for counts in first]
    qs = benjamini_hochberg(ps)
    found = [
        Comparison(m, s, t, r, "first", *counts, p, q, q < Q)
        for (m, s, t, r), counts, p, q in zip(tests, first, ps, qs, strict=True)
    ]
    pending = [
        i
        for i, c in enumerate(found)
        # in whole replies of FIRST: |h/n - r/m| * FIRST >= SCREEN, cross-multiplied so it's exact
        if not c.passes
        and abs(c.hits * c.reference_n - c.reference_hits * c.n) * FIRST >= SCREEN * c.n * c.reference_n
    ]
    fresh = {
        i: (
            *get((found[i].model, found[i].target), "fresh"),
            *get((found[i].model, found[i].reference), "fresh"),
        )
        for i in pending
    }
    ran = [i for i in pending if fresh[i][1] and fresh[i][3]]
    # every pending test counts in the correction; one that didn't run enters at p = 1 and never passes
    fresh_ps = {i: fisher(*fresh[i]) if i in ran else 1.0 for i in pending}
    fresh_qs = dict(zip(pending, benjamini_hochberg([fresh_ps[i] for i in pending]), strict=True))
    for i, p, q in ((i, fresh_ps[i], fresh_qs[i]) for i in ran):
        found[i] = found[i]._replace(
            stage="fresh",
            hits=fresh[i][0],
            n=fresh[i][1],
            reference_hits=fresh[i][2],
            reference_n=fresh[i][3],
            p=p,
            q=q,
            passes=q < Q,
        )
    for i in set(pending) - set(ran):
        found[i] = found[i]._replace(stage="unconfirmed")
    return found


def sanity_checks(rows: list[dict]) -> list[Comparison]:
    """One owner over both firms against the bare start, on the first stage's replies, outside the family's
    correction: q is p."""
    hits, n, models = counted(rows)
    found = []
    for model in models:
        for start in DUOPOLY_STARTS:
            target = f"id_{start}_{SANITY}"
            if target not in CELLS:
                continue
            reference = f"id_{start}_base"
            counts = (
                hits.get((model, target, "first"), 0),
                n[(model, target, "first")],
                hits.get((model, reference, "first"), 0),
                n[(model, reference, "first")],
            )
            p = fisher(*counts)
            found.append(Comparison(model, start, target, reference, "first", *counts, p, p, p < Q))
    return found
