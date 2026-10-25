"""Where the models answer differently (#41): in each of IDL-1's duopoly cells, whether the models' answers at
the cartel share differ, and still differ with refusals set aside.

The models are those with every IDL-1 cell's first stage (`idl1.counted`), a reply's outcome `judge.outcome`.
The first stage tests each cell's first FIRST replies a model twice across the models, by
Fisher-Freeman-Halton on the 2 x k table with its margins fixed: the share of replies at the cartel share, and
the same share among the answers that aren't refusals (a model with none left sits that one out).
Benjamini-Hochberg across the cells for each test; a cell passes when both q < Q. A passing cell is tested
again on its fresh replies alone, Benjamini-Hochberg across the cells tested again; one where a model lacks
fresh replies is unconfirmed and enters that correction at p = 1. The paper's appendix draws the cells the
fresh replies confirm."""

import math
from collections.abc import Iterator
from typing import NamedTuple

from zerocommcartel.criteria.communal.identity import CELLS
from zerocommcartel.criteria.communal.idl1 import (
    DUOPOLY_CELLS,
    Outcomes,
    Q,
    Stage,
    Tally,
    answered,
    benjamini_hochberg,
    counted,
    outcomes,
)


class Split(NamedTuple):
    model: str
    cartel: int  # replies at the cartel share
    refusals: int
    n: int  # replies

    @property
    def answers(self) -> int:
        """The replies that aren't refusals."""
        return self.n - self.refusals


class CellVerdict(NamedTuple):
    cell: str
    stage: (
        Stage  # whose replies the verdict used; "unconfirmed": passed the first stage, fresh replies missing
    )
    splits: tuple[Split, ...]  # one a model
    choice_p: float  # the share at the cartel share
    choice_q: float
    aside_p: float  # the same share among the answers that aren't refusals
    aside_q: float
    passes: bool


def exact_two_row(hits: list[int], ns: list[int]) -> float:
    """Fisher-Freeman-Halton for a 2 x k table, exactly: the chance, margins fixed, of a table no likelier
    than this one, by enumerating every split of the hits."""

    def weight(xs: tuple[int, ...]) -> int:
        return math.prod(math.comb(n, x) for n, x in zip(ns, xs, strict=True))

    observed, total = weight(tuple(hits)), sum(hits)
    found = sum(w for xs in _divisions(total, ns) if (w := weight(xs)) <= observed)
    return found / math.comb(sum(ns), total)


def split(found: Outcomes, model: str, cell: str, stage: Stage) -> Split:
    """A model's replies in a cell and stage, split by outcome. Raises when one is off the cartel share and
    the refusal judge hasn't labelled it."""
    answers = answered(found, model, cell, stage)
    replies = len(found.get((model, cell, stage), []))
    return Split(model, answers.hits, replies - answers.n, replies)


def tested(cell: str, splits: list[Split], stage: Stage) -> CellVerdict:
    """The cell's two p-values, its q-values and verdict left for the correction to fill in."""
    choice = exact_two_row([s.cartel for s in splits], [s.n for s in splits])
    kept = [s for s in splits if s.answers]
    aside = exact_two_row([s.cartel for s in kept], [s.answers for s in kept]) if len(kept) > 1 else 1.0
    return CellVerdict(cell, stage, tuple(splits), choice, 1.0, aside, 1.0, False)


def corrected(found: list[CellVerdict]) -> list[CellVerdict]:
    """Benjamini-Hochberg across the verdicts for each test; both q < Q passes."""
    choice = benjamini_hochberg([v.choice_p for v in found])
    aside = benjamini_hochberg([v.aside_p for v in found])
    return [
        v._replace(choice_q=c, aside_q=a, passes=c < Q and a < Q)
        for v, c, a in zip(found, choice, aside, strict=True)
    ]


def start_of(cell: str) -> str | None:
    """The cell's nothing-said start, with the same start and question; None when that is the cell itself."""
    c = CELLS[cell]
    start = f"id_{c.start}_base" + ("_own" if c.ask == "own" else "")
    return start if start in CELLS and start != cell else None


def screened(rows: list[dict]) -> list[str]:
    """The cells whose first stage passes the share test alone, with no refusal labels: a superset of the
    cells `verdicts` tests again, since its refusal test can only remove cells."""
    tallies, models = counted(rows)
    if len(models) < 2:
        return []

    def unjudged(model: str, cell: str) -> Split:  # every reply counted as an answer, none as a refusal
        hits, n = tallies.get((model, cell, "first"), Tally(0, 0))
        return Split(model, hits, 0, n)

    found = corrected([tested(cell, [unjudged(m, cell) for m in models], "first") for cell in DUOPOLY_CELLS])
    return [v.cell for v in found if v.choice_q < Q]


def first_stage(rows: list[dict], labels: dict[str, dict]) -> list[CellVerdict]:
    """Each duopoly cell's first-stage verdict, in `DUOPOLY_CELLS` order: both tests on its first FIRST
    replies a model, corrected across the cells. Needs labels for those replies only."""
    _, models = counted(rows)
    if len(models) < 2:
        return []
    replies = outcomes(rows, labels)
    return corrected(
        [tested(c, [split(replies, m, c, "first") for m in models], "first") for c in DUOPOLY_CELLS]
    )


def verdicts(rows: list[dict], labels: dict[str, dict]) -> list[CellVerdict]:
    """Each duopoly cell's verdict, in `DUOPOLY_CELLS` order, by the rule in the module's docstring."""
    first = first_stage(rows, labels)
    if not first:
        return []
    _, models = counted(rows)
    replies = outcomes(rows, labels)
    pending = [i for i, v in enumerate(first) if v.passes]
    ran = {i for i in pending if all(replies.get((m, first[i].cell, "fresh")) for m in models)}
    fresh = corrected(
        [
            tested(first[i].cell, [split(replies, m, first[i].cell, "fresh") for m in models], "fresh")
            if i in ran
            else first[i]._replace(choice_p=1.0, aside_p=1.0)
            for i in pending
        ]
    )
    found = list(first)
    for i, verdict in zip(pending, fresh, strict=True):
        found[i] = verdict if i in ran else first[i]._replace(stage="unconfirmed", passes=False)
    return found


def _divisions(total: int, ns: list[int]) -> Iterator[tuple[int, ...]]:
    """Every way to divide `total` hits among columns of `ns` replies."""
    if len(ns) == 1:
        if 0 <= total <= ns[0]:
            yield (total,)
        return
    for x in range(min(total, ns[0]) + 1):
        for rest in _divisions(total - x, ns[1:]):
            yield (x, *rest)
