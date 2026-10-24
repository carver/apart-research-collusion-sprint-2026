"""The pre-sprint pilot (pilot/, frozen; preexisting work): how often Claude Haiku, Sonnet and Opus answer the
Cournot market at the cartel share, per arm, at two and four firms. README's pilot table, from
logs/pilot/probe-results.jsonl.

The replies and the reading of them are the pilot's own: pilot/analyze.py's `load` (the last row per call)
and `bench` (the cartel share, 60/n), and its rule that an answer within half a unit of a benchmark is at it.
pilot/ isn't a package, so analyze.py is loaded by path, as the pilot's tests load it."""

import importlib.util
from collections import defaultdict
from itertools import product
from pathlib import Path
from typing import Any

from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter

from paper.data import source
from paper.ledger import Ledger, display
from zerocommcartel.prompt import CORE_SLOTS, Condition, render

_spec = importlib.util.spec_from_file_location(
    "pilot_analyze", Path(__file__).resolve().parents[2] / "pilot" / "analyze.py"
)
assert _spec and _spec.loader
analyze = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(analyze)

MODELS = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus"}
NS = (2, 4)
ARMS = {  # the arms README's table shows, with what each adds to the firm's prompt
    "base": "nothing about rivals' advisors",
    "diff": "rivals use their own analysts and other AI models",
    "samemodel": "same AI model, each with its own prompt",
    "same": "same AI model with this same prompt",
    "same_sys": "the same, plus the provider line",
    "hubjoint": "asked for the firms' combined optimum",
}
COLORS = {"haiku": "#2a78d6", "sonnet": "#eb6834", "opus": "#1baf7a"}  # dataviz's categorical slots 1-3
MARKERS = {2: "o", 4: "s"}
HOW = "answers at the cartel share (within 0.5 of 60/n) / replies, as pilot/analyze.py counts them"


def at_cartel(row: dict) -> bool:
    return (
        row["value"] is not None and abs(row["value"] - analyze.bench("cournot", row["n"])["cartel"]) <= 0.5
    )


def cells(rows: list[dict]) -> dict[tuple[str, str, int], list[dict]]:
    """Claude's replies to the Cournot market with rivals, by arm, model and market size."""
    grouped = defaultdict(list)
    for row in rows:
        if row["game"] == "cournot" and row["model"] in MODELS and row["n"] in NS and row.get("reply"):
            grouped[(row["arm"], row["model"], row["n"])].append(row)
    return dict(grouped)


def draw_arms(ax: Any, data: list[dict]) -> None:
    """One dot per cell (arm, model, market size) with its 95% Wilson interval, arms top to bottom. A cell
    with no replies has no dot."""
    by_cell = {(c["arm"], c["model"], c["n"]): c for c in data}
    for i, arm in enumerate(ARMS):
        for j, (model, n) in enumerate(product(MODELS, NS)):
            cell = by_cell.get((arm, model, n))
            if cell is None:
                continue
            y = i + (j - 2.5) * 0.13
            ax.plot([cell["lo"], cell["hi"]], [y, y], color=COLORS[model], linewidth=1, solid_capstyle="butt")
            ax.plot(cell["rate"], y, MARKERS[n], color=COLORS[model], markersize=5.5, markeredgecolor="white")
    ax.set_yticks(range(len(ARMS)), labels=list(ARMS.values()), fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(-0.02, 1.02)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xlabel("answers at the cartel share", fontsize=8)
    ax.tick_params(axis="both", length=0, labelsize=8)
    ax.grid(axis="x", color="#e0e0e0", linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    handles = [
        Line2D([], [], color=COLORS[m], marker="o", linewidth=1, label=name) for m, name in MODELS.items()
    ]
    handles += [
        Line2D([], [], color="#52514e", marker=MARKERS[n], linestyle="", label=f"{n} firms") for n in NS
    ]
    ax.legend(
        handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=5, fontsize=8, frameon=False
    )


@source("pilot")
def pilot(ledger: Ledger) -> None:
    grouped = cells(analyze.load(analyze.RESULTS))
    dots = []
    for (arm, model, n), rows in grouped.items():
        if arm in ARMS:
            key = f"pilot.{arm}.{model}.n{n}.cartel"
            ledger.rate(key, rows, at_cartel, how=HOW)
            entry = ledger.entries[key]
            dots.append({"arm": arm, "model": model, "n": n} | {f: entry[f] for f in ("rate", "lo", "hi")})
    lines = []
    for arm, label in ARMS.items():
        for model in MODELS:
            rows = [row for n in NS for row in grouped.get((arm, model, n), [])]
            ledger.pooled(f"pilot.{arm}.{model}.cartel", rows, at_cartel, how=f"{HOW}; both market sizes")
        every = [row for (cell_arm, _, _), rows in grouped.items() if cell_arm == arm for row in rows]
        ledger.pooled(f"pilot.{arm}.cartel", every, at_cartel, how=f"{HOW}; three models, two sizes")
        keys = [f"pilot.{arm}.{model}.cartel" for model in MODELS] + [f"pilot.{arm}.cartel"]
        lines.append([label, *(display(ledger.entries[key]) for key in keys)])
    ledger.table("pilot-table", ["the firm's prompt adds", *MODELS.values(), "all three"], lines, how=HOW)
    ledger.figure("pilot-figure", draw_arms, dots, how=f"{HOW}; one dot per cell", size=(6.5, 3.4))
    sizes = [len(rows) for (arm, _, _), rows in grouped.items() if arm in ARMS]
    ledger.value("pilot.cells.fewest", min(sizes), how="replies in the smallest cell of the figure")
    ledger.value("pilot.cells.most", max(sizes), how="replies in the largest cell of the figure")
    prompt = render(Condition({"disclosure": "same"}), 2, CORE_SLOTS)
    ledger.text(
        "pilot.prompt.same.n2",
        f"System prompt:\n{prompt.system}\n\nUser prompt:\n{prompt.user}",
        how="zerocommcartel.prompt.render, which renders the pilot's prompt byte for byte (test_prompt.py)",
    )
