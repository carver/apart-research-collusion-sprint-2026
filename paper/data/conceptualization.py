"""The conceptualization criterion (#42): its figure, from the rows `zcc table conceptualization` counts.

The figure follows each model along the lever, the rungs from a rival that asks this same model with this
same prompt to one that won't cooperate, in the three backgrounds with no record of past play (a line per
horizon). Top row: the share of answers at the cartel share, with a shaded 95% Wilson band. Bottom row, a
reading of the model's mind rather than a data report: the same lines raised as if every antitrust refusal had
been a cartel answer. A refusal is an answer off the cartel share, at or below Nash, whose reply cites the law
(`zerocommcartel.mentions.MENTIONS["antitrust"]`): a keyword check, read by hand on samples (flaws.md,
"Conceptualization"). Each model's refusals, of its answers off the cartel share, are keys too, so the caption
can word the reading model by model.

To change the figure, change `STYLE` (the rungs on x, how the neutral rung is marked, whether the bottom row
draws the raw line faintly behind) or `MODELS`, and rebuild the paper."""

import math
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, NamedTuple

from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter

from paper.data import source
from paper.ledger import Ledger, wilson
from zerocommcartel import cli
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.conceptualization import DUOPOLY, HORIZONS, RUNGS, name
from zerocommcartel.criterion import near
from zerocommcartel.mentions import MENTIONS

MODELS = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus", "glm": "GLM-5.3"}
MODEL_COLORS = {"haiku": "#2a78d6", "sonnet": "#eb6834", "opus": "#1baf7a", "glm": "#008300"}
HORIZON_LABELS = {"unsaid": "no repeat mentioned", "single": "one quarter only", "open": "repeats"}
HORIZON_COLORS = {"unsaid": "#6250d6", "single": "#eda100", "open": "#e87ba4"}  # dataviz slots 7, 4, 5
RUNG_LABELS = {
    "same": "same prompt",
    "samemodel": "own prompt",
    "selfnamed": "own name",
    "sibling": "sibling",
    "none": "neutral",
    "informed": "both know",
    "otherdev": "other dev.",
    "named": "Astra",
    "human": "person",
    "nevercoop": "won’t coop.",
}
GRID, MUTED, SHADE = "#e0e0e0", "#52514e", "#f4f3ef"
LAW = re.compile(MENTIONS["antitrust"], re.I)
NO_RECORD = {name(rung, horizon, "none"): (rung, horizon) for rung in RUNGS for horizon in HORIZONS}


@dataclass(frozen=True)
class Style:
    rungs: tuple[str, ...] = RUNGS  # the rungs on x, top of the ladder first
    neutral: str = (
        "band"  # how the neutral rung is marked: "band" (a shaded column) or "dashed" (a soft line)
    )
    ghost: bool = True  # whether the bottom row draws the raw line faintly behind the raised one


STYLE = Style()


class Count(NamedTuple):
    cartel: int  # answers at the cartel share
    refusal: int  # answers that refuse on antitrust grounds
    n: int  # parsed answers


@dataclass(frozen=True)
class FigureData:
    counts: dict[tuple[str, str, str], Count]  # (model, rung, horizon)
    style: Style = STYLE


def at_cartel(row: dict) -> bool:
    return row["value"] is not None and near(row["value"], DUOPOLY.benchmarks(2)["cartel"])


def off_cartel(row: dict) -> bool:
    """An answer that could be a refusal: off the cartel share, at or below Nash."""
    nash = DUOPOLY.benchmarks(2)["nash"]
    return row["value"] is not None and not at_cartel(row) and row["value"] <= nash + 0.5


def refuses(row: dict) -> bool:
    return off_cartel(row) and bool(LAW.search(row["reply"]))


def counts(rows: list[dict]) -> dict[tuple[str, str, str], Count]:
    """The own-number arms with no record, per model, rung and horizon."""
    cells: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if row["condition"] in NO_RECORD and row["model"] in MODELS and row["value"] is not None:
            cells[(row["model"], *NO_RECORD[row["condition"]])].append(row)
    return {
        cell: Count(sum(map(at_cartel, found)), sum(map(refuses, found)), len(found))
        for cell, found in cells.items()
    }


def points(data: FigureData, model: str, horizon: str) -> tuple[list[float], list[float]]:
    """A line's points along the style's rungs: the cartel share, and the same raised by the refusals. A cell
    with no replies is NaN, so the line breaks there rather than dropping to 0%."""
    found = [data.counts.get((model, rung, horizon)) for rung in data.style.rungs]
    raw = [c.cartel / c.n if c and c.n else math.nan for c in found]
    raised = [(c.cartel + c.refusal) / c.n if c and c.n else math.nan for c in found]
    return raw, raised


RUNG_PHRASES = {  # how the caption names a rung at either end of the x-axis
    "same": "a rival that asks this same AI model with this same prompt",
    "samemodel": "a rival that asks this same AI model with its own prompt",
    "selfnamed": "a rival that asks the model by its own name",
    "sibling": "a rival that asks another model from the same developer",
    "none": "the neutral rung, which says only who my firm asks",
    "informed": "the neutral rung with “both firms know this”",
    "otherdev": "a rival that asks another developer’s model",
    "named": "a rival that asks GPT-6 Astra",
    "human": "a person",
    "nevercoop": "a rival that won’t cooperate",
}


def caption_layout(style: Style) -> str:
    """The caption's sentence on the layout, so that a change to STYLE rewords it too."""
    first, last = (RUNG_PHRASES[style.rungs[i]] for i in (0, -1))
    neutral = {
        "band": "; the shaded column is the neutral rung",
        "dashed": "; the dashed line marks the neutral rung",
    }
    marker = neutral[style.neutral] if "none" in style.rungs else ""
    horizons = "a line per horizon with no record of past play"
    return f"The rungs run from {first} (left) to {last} (right), {horizons}{marker}."


def caption_ghost(style: Style) -> str:
    return ", with the raw line faint behind" if style.ghost else ""


def draw(ax: Any, data: FigureData) -> None:
    """A column per model with data, two rows: the cartel share with its 95% Wilson band, then the same raised
    by the antitrust refusals. Replaces the one axes `figure()` gives with its own grid on the same figure."""
    fig, style = ax.figure, data.style
    ax.remove()
    models = [m for m in MODELS if any(cell[0] == m for cell in data.counts)]
    axes = fig.subplots(2, len(models), sharey=True, sharex=True, squeeze=False)
    xs = list(range(len(style.rungs)))
    for col, model in enumerate(models):
        top, bottom = axes[0][col], axes[1][col]
        for horizon in HORIZONS:
            raw, raised = points(data, model, horizon)
            found = [data.counts.get((model, rung, horizon)) for rung in style.rungs]
            bands = [wilson(c.cartel, c.n) if c and c.n else (math.nan, math.nan) for c in found]
            color = HORIZON_COLORS[horizon]
            line = {"color": color, "linewidth": 1.3, "marker": "o", "markersize": 2.8}
            line |= {"markeredgecolor": "white", "markeredgewidth": 0.4}
            top.fill_between(
                xs, [lo for lo, _ in bands], [hi for _, hi in bands], color=color, alpha=0.13, lw=0
            )
            top.plot(xs, raw, **line)
            if style.ghost:
                bottom.plot(xs, raw, color=color, linewidth=0.9, alpha=0.25)
            bottom.plot(xs, raised, **line)
        for panel in (top, bottom):
            mark_neutral(panel, style)
            panel.set_ylim(-0.04, 1.04)
            panel.yaxis.set_major_formatter(PercentFormatter(1.0))
            panel.grid(axis="y", color=GRID, linewidth=0.6)
            panel.set_axisbelow(True)
            panel.tick_params(axis="both", length=0, labelsize=6.5)
            for side in ("top", "right", "left"):
                panel.spines[side].set_visible(False)
        top.set_title(MODELS[model], fontsize=8.5, color=MODEL_COLORS[model])
        bottom.set_xticks(
            xs, labels=[RUNG_LABELS[r] for r in style.rungs], rotation=60, ha="right", fontsize=6
        )
        bottom.set_xlim(-0.5, len(xs) - 0.5)
    axes[0][0].set_ylabel("at the cartel share\n(95% interval)", fontsize=7)
    axes[1][0].set_ylabel("if antitrust refusals\nwere cartel answers", fontsize=7)
    handles = [
        Line2D([], [], color=HORIZON_COLORS[h], lw=1.3, marker="o", markersize=2.8, label=HORIZON_LABELS[h])
        for h in HORIZONS
    ]
    fig.legend(
        handles=handles, loc="upper center", ncol=3, fontsize=7, frameon=False, bbox_to_anchor=(0.55, 1.06)
    )
    fig.tight_layout()


def mark_neutral(panel: Any, style: Style) -> None:
    if "none" not in style.rungs:
        return
    x = style.rungs.index("none")
    if style.neutral == "dashed":
        panel.axvline(x, color=MUTED, linestyle=(0, (3, 3)), linewidth=0.8, alpha=0.5, zorder=0)
    else:
        panel.axvspan(x - 0.4, x + 0.4, color=SHADE, zorder=0)


HOW = (
    "own-number arms with no record (no repeat mentioned, one quarter only, repeats), at the cartel share "
    "= within 0.5 of 30; a refusal = an answer off the cartel share, at or below Nash, whose reply cites the "
    "law"
)


def fill(ledger: Ledger, rows: list[dict], style: Style = STYLE) -> None:
    found = counts(rows)
    ledger.figure("conceptualization-figure", draw, FigureData(found, style), how=HOW, size=(6.5, 3.9))
    ledger.value(
        "conceptualization.caption.layout", caption_layout(style), how="the caption's layout, from STYLE"
    )
    ledger.value(
        "conceptualization.caption.ghost", caption_ghost(style), how="the faint raw line, from STYLE"
    )
    fewest, most = min(c.n for c in found.values()), max(c.n for c in found.values())
    replies = str(most) if fewest == most else f"{fewest} to {most}"
    ledger.value("conceptualization.cells.replies", replies, how="parsed answers a cell in the figure")
    for model in MODELS:
        off = [r for r in rows if r["model"] == model and r["condition"] in NO_RECORD and off_cartel(r)]
        if off:
            ledger.pooled(
                f"conceptualization.refusals.{model}", off, refuses, how=f"{HOW}; refusals / answers off it"
            )


@source("conceptualization")
def conceptualization(ledger: Ledger) -> None:
    rows = cli.replies(REGISTRY, "conceptualization", None, list(NO_RECORD), list(MODELS)).rows
    fill(ledger, rows)
