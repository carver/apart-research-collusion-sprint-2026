"""Where the models answer differently (#41): the appendix figure of the IDL-1 cells whose models differ in
their answers at the cartel share, with refusals counted and with them set aside, confirmed on fresh replies
(`zerocommcartel.criteria.communal.crossmodel.verdicts`, whose docstring gives the rule).

One row per confirmed cell. A dot per model: its share at the cartel share among its fresh answers that aren't
refusals, with a Wilson 95% whisker; hollow, the same model in the cell's nothing-said start (the same start
and question), from that start's fresh replies. A model that refused every fresh answer is named instead of
drawn, its start still shown; a point on fewer than THIN answers is faded, and each point's count is printed
at the right, the start's in parentheses."""

from typing import Any, NamedTuple

from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

from paper.data import source
from paper.data.idl1 import ARM_LABELS, GRID, INK, MODELS, MUTED, START_LABELS
from paper.data.pilot import COLORS as PILOT_COLORS
from paper.ledger import Ledger
from zerocommcartel import cli, logs
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.communal.crossmodel import Split, split, verdicts
from zerocommcartel.criteria.communal.identity import CELLS, STARTS
from zerocommcartel.criteria.communal.idl1 import FIRST, FOLDER, Q, outcomes, wilson_share
from zerocommcartel.criteria.communal.judge import REFUSAL
from zerocommcartel.judge import load_labels

COLORS = PILOT_COLORS | {"glm": "#eda100", "astra": "#e87ba4"}  # dataviz's categorical slots 4 and 5
MARKERS = {"haiku": "o", "sonnet": "s", "opus": "D", "glm": "^", "astra": "v"}
THIN = 5  # a point on fewer answers than this is faded
HOW = "IDL-1's cells confirmed on fresh replies, from logs/communal/idl1/ (communal.crossmodel.verdicts)"


def start_of(cell: str) -> str | None:
    """The cell's nothing-said start, with the same start and question; None when that is the cell itself."""
    c = CELLS[cell]
    start = f"id_{c.start}_base" + ("_own" if c.ask == "own" else "")
    return start if start in CELLS and start != cell else None


def label(cell: str) -> str:
    """The cell as the figure names it, the way Figure 1 names starts and identities."""
    c = CELLS[cell]
    return f"{START_LABELS[c.start]}: {ARM_LABELS[c.identity]}" + (
        ", asked for profit" if c.ask == "own" else ""
    )


def faded(answers: int) -> float:
    """A point's opacity: faded when it rests on fewer than THIN answers."""
    return 0.3 if answers < THIN else 1.0


class Row(NamedTuple):
    label: str
    splits: tuple[Split, ...]  # the cell's fresh replies, a model each
    starts: dict[str, Split]  # model: its fresh replies in the cell's nothing-said start


class FigureData(NamedTuple):
    rows: list[Row]


def point(ax: Any, at: float, s: Split, start: Split | None) -> None:
    """One model's dot, whisker, hollow start and counts (the start's in parentheses), on the row's line `at`.
    A model with no answer left is named, its start still drawn."""
    counts = []
    if s.answers:
        low, high = wilson_share(s.cartel, s.answers)
        ax.plot([low, high], [at, at], color=COLORS[s.model], linewidth=0.8, alpha=0.6 * faded(s.answers))
        ax.scatter(
            s.cartel / s.answers,
            at,
            marker=MARKERS[s.model],
            s=22,
            color=COLORS[s.model],
            edgecolor="white",
            linewidth=0.4,
            zorder=3,
            alpha=faded(s.answers),
        )
        counts.append(f"{s.cartel}/{s.answers}")
    else:
        ax.text(0, at, f"{MODELS[s.model]}: all refused", va="center", fontsize=5.4, color=MUTED)
    if start and start.answers:
        ax.scatter(
            start.cartel / start.answers,
            at,
            marker=MARKERS[s.model],
            s=16,
            facecolor="white",
            edgecolor=COLORS[s.model],
            linewidth=0.7,
            zorder=2,
            alpha=faded(start.answers),
        )
        counts.append(f"({start.cartel}/{start.answers})")
    text = " ".join(counts)
    ax.text(1.04, at, text, va="center", fontsize=5.4, color=MUTED, transform=ax.get_yaxis_transform())


def draw(ax: Any, data: FigureData) -> None:
    """One row per cell, the models' points spread across it; an empty axes when no cell is confirmed."""
    if not data.rows:  # nothing confirmed: the caption says so
        ax.axis("off")
        return
    models = [s.model for s in data.rows[0].splits]
    step = 0.6 / max(len(models) - 1, 1)
    offsets = {m: -0.3 + i * step for i, m in enumerate(models)}
    for y, row in enumerate(data.rows):
        for s in row.splits:
            point(ax, y + offsets[s.model], s, row.starts.get(s.model))
    ax.set_yticks(range(len(data.rows)), [row.label for row in data.rows], fontsize=7, color=INK)
    ax.set_ylim(len(data.rows) - 0.5, -0.6)
    ax.set_xlim(-0.02, 1.02)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0, labelsize=7)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.set_xlabel("at the cartel share, of the fresh answers that aren't refusals", fontsize=7, color=MUTED)
    handles = [
        Line2D([], [], marker=MARKERS[m], color=COLORS[m], linewidth=0, label=MODELS[m]) for m in models
    ]
    handles.append(
        Line2D([], [], marker="o", color=MUTED, markerfacecolor="white", linewidth=0, label="nothing said")
    )
    ax.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.45, 1.0),
        ncol=len(handles),
        frameon=False,
        fontsize=7,
    )


def fill(ledger: Ledger, rows: list[dict], labels: dict[str, dict]) -> None:
    found = verdicts(rows, labels)
    replies = outcomes(rows, labels)
    confirmed = [v for v in found if v.stage == "fresh" and v.passes]
    order = list(STARTS)
    confirmed.sort(
        key=lambda v: (order.index(CELLS[v.cell].start), CELLS[v.cell].identity is not None, label(v.cell))
    )
    drawn = []
    for v in confirmed:
        start = start_of(v.cell)
        starts = {
            s.model: split(replies, s.model, start, "fresh")
            for s in v.splits
            if start and replies.get((s.model, start, "fresh"))
        }
        drawn.append(Row(label(v.cell), v.splits, starts))
    points = len(found[0].splits) * len(drawn) if found else 0
    ledger.figure("idl1-cross-figure", draw, FigureData(drawn), how=HOW, size=(6.5, 0.15 * points + 0.9))
    ledger.value(
        "idl1.cross.caption.none",
        "" if drawn else "No cell holds on its fresh replies.",
        how="the note when no cell is confirmed",
    )
    ledger.value("idl1.cross.cells", len(found), how="IDL-1's duopoly cells tested across the models")
    ledger.value(
        "idl1.cross.first",
        sum(v.stage != "first" for v in found),
        how=f"cells passing both tests on their first {FIRST} replies a model",
    )
    ledger.value(
        "idl1.cross.confirmed", len(confirmed), how="of those, cells passing both again on fresh replies"
    )
    ledger.value(
        "idl1.cross.unconfirmed",
        sum(v.stage == "unconfirmed" for v in found),
        how="cells passing the first stage whose fresh replies are missing for a model",
    )
    fresh = sorted({s.n for v in found if v.stage == "fresh" for s in v.splits}) or [0]
    ledger.value(
        "idl1.cross.fresh",
        fresh[0] if len(fresh) == 1 else f"{fresh[0]} to {fresh[-1]}",
        how="fresh replies a model in a cell tested again",
    )
    ledger.value("idl1.cross.first-n", FIRST, how="replies a model in a cell in the first stage")
    ledger.value("idl1.cross.thin", THIN, how="answers below which a point is faded")
    ledger.value("idl1.cross.q", f"{Q:.2f}", how="Benjamini-Hochberg's bar")


@source("idl1-cross")
def idl1_cross(ledger: Ledger) -> None:
    # every IDL-1 cell, since verdicts keeps the models with every cell's first stage complete
    log = logs.experiment_log(FOLDER)
    rows = cli.replies(REGISTRY, "communal", str(log), list(CELLS), None).rows
    fill(ledger, rows, load_labels(REFUSAL, logs.judge_path(log, REFUSAL.name)))
