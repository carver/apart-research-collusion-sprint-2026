"""The compliant criterion (#40): CPL-9, the company's environment in the realistic market, from
logs/compliant/cpl9.

The figure is the single-axis cells, one sentence added to CAP-9's own prompt at a time, and one cell with two
at once, the only one that ends GLM-5.3's collusion. Every count is the replies whose answer is exactly the
cartel quantity, 20, of all the cell's replies, as paper/data/capable.py counts them."""

from typing import Any

from matplotlib.ticker import PercentFormatter

from paper.data import source
from paper.data.capable import GRID, INK, MUTED, at_cartel, style
from paper.ledger import Ledger
from zerocommcartel import cli
from zerocommcartel.criteria import REGISTRY

MODELS = {"opus": "Opus", "astra": "GPT-6 Astra", "glm": "GLM-5.3"}
TOWARD, AWAY = "#2a78d6", "#e34948"  # dataviz's diverging poles, as idl1's figure
TOWARD_BAND, AWAY_BAND, PLAIN_BAND = "#d6e4f4", "#f7dbda", "#e9e8e3"
SURFACE = "#fcfcfb"
CONTROL = "quarter_none_none_none"
ROWS = [  # (condition, label); a None condition is a group's heading
    (CONTROL, "Control"),
    (None, "oversight"),
    ("quarter_investigating_none_none", "an authority is investigating"),
    ("quarter_rarely_none_none", "the authority rarely looks"),
    ("quarter_nobody_none_none", "nobody watches"),
    ("quarter_management_none_none", "management will review"),
    (None, "a tool"),
    ("quarter_none_report_none", "REPORT_COLLUSION line"),
    ("quarter_none_flag_none", "FLAG line"),
    ("quarter_none_support_none", "IT_SUPPORT line"),
    (None, "the last quarter, called"),
    ("quarter_none_none_illegal", "“illegally colluded”"),
    ("quarter_none_none_cartel", "“a tacit cartel”"),
    ("quarter_none_none_optimized", "“optimized their output”"),
    (None, "two at once (10 replies a cell)"),
    ("quarter_investigating_none_illegal", "investigating + “illegally”"),
]
CITED = ["quarter_none_report_illegal"]  # cells the text cites that the figure doesn't draw
LOG = "logs/compliant/cpl9/results.jsonl"
SHOWN = 0.04  # a change smaller than this draws no arrow
HOW = "answers exactly at the cartel quantity (20) / replies"


def key(model: str, condition: str) -> str:
    return f"cpl9.{model}.{condition.removeprefix('quarter_')}"


def draw(ax: Any, cells: dict[tuple[str, str], dict]) -> None:
    """A panel per model, a row per sentence: an arrow from the model's control (hollow) to its share with
    the sentence (filled), each with its 95% Wilson band; red where the share falls, blue where it rises.
    Replaces the one axes `figure()` gives with its own panels."""
    fig = ax.figure
    ax.remove()
    grid = fig.subplots(1, len(MODELS), sharey=True)
    fig.subplots_adjust(wspace=0.12)
    ys, y = [], 0.0
    for condition, _ in ROWS:
        y += 0.45 if condition is None else 0
        ys.append(y)
        y += 1
    for panel, model in zip(grid, MODELS, strict=True):
        control = cells[(model, CONTROL)]
        for y, (condition, _) in zip(ys, ROWS, strict=True):
            if condition is None:
                continue
            cell = cells[(model, condition)]
            change = cell["rate"] - control["rate"]
            color, band = (
                (AWAY, AWAY_BAND) if change < 0 else (TOWARD, TOWARD_BAND) if change > 0 else (MUTED, None)
            )
            panel.plot(
                [control["lo"], control["hi"]],
                [y, y],
                color=PLAIN_BAND,
                linewidth=3.2,
                zorder=1,
                solid_capstyle="round",
            )
            hollow = {"markerfacecolor": SURFACE, "markeredgecolor": MUTED, "zorder": 4}
            if condition == CONTROL:
                panel.plot(control["rate"], y, "o", markersize=5, markeredgewidth=1, **hollow)
                continue
            if band:
                panel.plot(
                    [cell["lo"], cell["hi"]],
                    [y, y],
                    color=band,
                    linewidth=3.2,
                    zorder=2,
                    solid_capstyle="round",
                )
            if abs(change) > SHOWN:
                arrow = {
                    "arrowstyle": "-|>",
                    "color": color,
                    "linewidth": 1.1,
                    "shrinkA": 3,
                    "shrinkB": 3,
                    "mutation_scale": 6,
                }
                panel.annotate(
                    "", xy=(cell["rate"], y), xytext=(control["rate"], y), arrowprops=arrow, zorder=3
                )
            panel.plot(control["rate"], y, "o", markersize=4.2, markeredgewidth=0.9, **hollow)
            panel.plot(
                cell["rate"],
                y,
                "o",
                color=color,
                markersize=4.6,
                markeredgecolor="white",
                markeredgewidth=0.7,
                zorder=5,
            )
        panel.set_xlim(-0.04, 1.04)
        panel.set_xticks([0, 0.5, 1])
        panel.xaxis.set_major_formatter(PercentFormatter(1.0))
        panel.grid(axis="x", color=GRID, linewidth=0.6)
        style(panel)
        panel.set_title(MODELS[model], fontsize=8, color=INK, fontweight="bold", loc="left")
    first = grid[0]
    first.set_yticks(ys, [label for _, label in ROWS])
    for tick, (condition, _) in zip(first.get_yticklabels(), ROWS, strict=True):
        tick.set_fontweight("bold" if condition is None else "normal")
        tick.set_fontsize(7 if condition is None else 6.5)
        tick.set_color(INK)
    first.set_ylim(max(ys) + 0.7, -0.7)
    panels = (grid[0].get_position().x0 + grid[-1].get_position().x1) / 2  # the middle of the three panels
    fig.text(
        panels,
        0.97,
        "One sentence can end collusion",
        ha="center",
        va="bottom",
        fontsize=9,
        color=INK,
        fontweight="bold",
    )
    fig.text(
        0.6,
        -0.02,
        "share of replies at the cartel share (20); hollow: the control; bands: Wilson 95%",
        ha="center",
        fontsize=6.5,
        color=MUTED,
    )


def fill(ledger: Ledger, rows: list[dict]) -> None:
    """A rate per model and figure row, and per cell the text cites, and the figure; rows from CPL-9's other
    cells are left out."""
    figured = {condition for condition, _ in ROWS if condition}
    cells: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        if row["condition"] in figured | set(CITED) and row["model"] in MODELS:
            cells.setdefault((row["model"], row["condition"]), []).append(row)
    for (model, condition), replies in cells.items():
        ledger.rate(key(model, condition), replies, at_cartel, how=HOW)
    shares = {cell: ledger.entries[key(*cell)] for cell in cells if cell[1] in figured}
    ledger.figure(
        "cpl9-figure", draw, shares, how=f"{HOW}; a row per sentence, a panel per model", size=(6.5, 4)
    )


@source("compliant")
def compliant(ledger: Ledger) -> None:
    conditions = [condition for condition, _ in ROWS if condition] + CITED
    fill(ledger, cli.replies(REGISTRY, "compliant", LOG, conditions, list(MODELS)).rows)
