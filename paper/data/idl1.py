"""The identity lever (IDL-1, #41): its figure and its table of tests, from the rows its experiment logged.

The figure draws only the comparisons that pass `zerocommcartel.criteria.communal.idl1.verdicts`, whose
docstring gives the rule and whose constants its numbers. One panel per model with a passing comparison; a bar
per comparison, the identity's share at the cartel share minus its reference's, from the replies its verdict
used, with Newcombe's 95% interval as a whisker. A bar that ends at 0% or 100% and is no longer than CAP is
marked *, since the floor or the ceiling may have cut it short. The table lists every test, then the sanity
checks (one owner over both firms against the bare start), which the correction leaves out."""

from typing import Any, NamedTuple

from matplotlib.ticker import FuncFormatter

from paper.data import source
from paper.ledger import Ledger
from zerocommcartel import cli, logs
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.communal.identity import CELLS, STARTS
from zerocommcartel.criteria.communal.idl1 import (
    FIRST,
    FOLDER,
    SCREEN,
    Comparison,
    Q,
    newcombe,
    sanity_checks,
    verdicts,
)

MODELS = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus", "astra": "GPT-6 Astra", "glm": "GLM-5.3"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e0e0e0"
TOWARD, AWAY = "#2a78d6", "#e34948"  # dataviz's diverging poles: toward the cartel share, away from it
START_LABELS = {
    "unsaid": "no repeat mentioned",
    "single": "one quarter only",
    "opennash": "repeats, after 40s",
    "open": "repeats",
    "mirror": "same prompt",
    "goodwill": "repeats, after 30s",
}
ARM_LABELS = {
    None: "nothing said",
    "rival_charity": "charity owns rival",
    "rival_holding": "holding co. owns rival",
    "rival_pe": "PE owns rival",
    "mine_charity": "charity owns my firm",
    "mine_holding": "holding co. owns my firm",
    "mine_pe": "PE owns my firm",
    "both_charity": "one charity owns both",
    "both_holding": "one holding co. owns both",
    "buyers_hospitals": "hospitals buy",
    "buyers_towns": "towns buy",
    "buyers_distributors": "distributors buy",
    "buyers_pe": "PE distributors buy",
    "harm": "harm sentence",
    "price": "price sentence",
    "legal": "rival sells legal services",
    "electrical": "rival sells electrical services",
}
CAP = 0.5  # a bar this long or shorter, ending at the floor or ceiling, is marked
HOW = "IDL-1's passing comparisons, from logs/communal/idl1/results.jsonl (communal.idl1.verdicts)"


def difference(c: Comparison) -> float:
    return c.hits / c.n - c.reference_hits / c.reference_n


def capped(c: Comparison) -> bool:
    """Whether the bar ends at 0% or 100% and is no longer than CAP: the floor or the ceiling may have
    stopped it."""
    return c.hits in (0, c.n) and abs(difference(c)) <= CAP


def arms(c: Comparison) -> str:
    """The comparison as the figure and the table name it: the identity against its reference."""
    return f"{ARM_LABELS[CELLS[c.target].identity]} vs {ARM_LABELS[CELLS[c.reference].identity]}"


def label(c: Comparison) -> str:
    return f"{START_LABELS[c.start]}: {arms(c)}{' *' if capped(c) else ''}"


class FigureData(NamedTuple):
    panels: dict[str, list[Comparison]]  # model: its passing comparisons, in drawing order


def draw(ax: Any, data: FigureData) -> None:
    """One panel per model, stacked; replaces the one axes `figure()` gives with its own grid."""
    if not data.panels:  # nothing passes: the caption names the models, the figure stays empty
        ax.axis("off")
        return
    fig = ax.figure
    ax.remove()
    models = list(data.panels)
    axes = fig.subplots(
        len(models),
        1,
        sharex=True,
        squeeze=False,
        gridspec_kw={"height_ratios": [len(data.panels[m]) for m in models]},
    )
    for panel, model in zip((row[0] for row in axes), models, strict=True):
        found = data.panels[model]
        for y, c in enumerate(found):
            d = difference(c)
            low, high = newcombe(c.hits, c.n, c.reference_hits, c.reference_n)
            panel.barh(y, d, height=0.6, color=TOWARD if d > 0 else AWAY, edgecolor="white", linewidth=0.8)
            panel.errorbar(
                d, y, xerr=[[d - low], [high - d]], fmt="none", ecolor=INK, elinewidth=0.7, capsize=2
            )
        panel.axvline(0, color=MUTED, linewidth=0.7)
        panel.set_yticks(range(len(found)), [label(c) for c in found], fontsize=6.5, color=INK)
        panel.set_ylim(len(found) - 0.5, -0.5)
        panel.set_xlim(-1.05, 1.05)
        panel.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x * 100:+.0f}" if x else "0"))
        panel.grid(axis="x", color=GRID, linewidth=0.6)
        panel.set_axisbelow(True)
        panel.tick_params(axis="both", length=0, labelsize=6.5)
        for side in ("top", "right", "left"):
            panel.spines[side].set_visible(False)
        panel.set_title(MODELS.get(model, model), fontsize=8, color=INK, loc="left")
    axes[-1][0].set_xlabel(
        "points at the cartel share: the identity minus its reference", fontsize=7, color=MUTED
    )


def table_row(c: Comparison, sanity: bool = False) -> list[str]:
    """A test's row; a sanity check has no q, and "holds" where it came out as expected."""
    verdict = ("holds" if sanity else "passes") if c.passes else ""
    return [
        MODELS.get(c.model, c.model),
        START_LABELS[c.start],
        arms(c),
        "sanity check" if sanity else c.stage,
        f"{c.reference_hits}/{c.reference_n} → {c.hits}/{c.n}",
        f"{c.p:.4f}",
        "" if sanity else f"{c.q:.3f}",
        verdict,
    ]


def fill(ledger: Ledger, rows: list[dict]) -> None:
    found = verdicts(rows)
    order = list(STARTS)
    passing = sorted((c for c in found if c.passes), key=lambda c: (order.index(c.start), difference(c)))
    models = list(dict.fromkeys(c.model for c in found))
    panels = {m: [c for c in passing if c.model == m] for m in models if any(c.model == m for c in passing)}
    bars = sum(len(v) for v in panels.values())
    ledger.figure(
        "idl1-figure", draw, FigureData(panels), how=HOW, size=(6.5, 0.2 * bars + 0.45 * len(panels) + 0.5)
    )
    without = [MODELS.get(m, m) for m in models if m not in panels]
    note = f"No comparison passes for {' or '.join(without)}." if without else ""
    ledger.value("idl1.caption.none", note, how="the models with no passing comparison, so no panel")
    ledger.value(
        "idl1.tests",
        len(found),
        how="tests in the family: identities against controls, controls against the bare start",
    )
    ledger.value("idl1.pass", len(passing), how=f"comparisons that pass (q < {Q:g})")
    ledger.value(
        "idl1.pass.first",
        sum(c.stage == "first" for c in passing),
        how=f"passing on a cell's first {FIRST} replies",
    )
    ledger.value(
        "idl1.pass.fresh", sum(c.stage == "fresh" for c in passing), how="passing on fresh replies alone"
    )
    ledger.value("idl1.first", FIRST, how="replies a cell in the first stage")
    ledger.value(
        "idl1.fresh", max((c.n for c in found if c.stage == "fresh"), default=0), how="fresh replies a cell"
    )
    ledger.value(
        "idl1.screen", SCREEN, how=f"replies of {FIRST} a comparison must move, short of passing, to be rerun"
    )
    ledger.value("idl1.q", f"{Q:.2f}", how="Benjamini-Hochberg's bar")
    ledger.value(
        "idl1.cap", round(CAP * 100), how="the longest bar, in points, that the floor or ceiling marks"
    )
    header = ["model", "start", "comparison", "stage", "reference → identity", "p", "q", "verdict"]
    table = [table_row(c) for c in found] + [table_row(c, sanity=True) for c in sanity_checks(rows)]
    ledger.table(
        "idl1-tests",
        header,
        table,
        how="every test with its counts, p, q and verdict, then the sanity checks",
    )


@source("idl1")
def idl1(ledger: Ledger) -> None:
    # every model in the log; verdicts keeps those with every cell's first stage complete
    rows = cli.replies(REGISTRY, "communal", str(logs.experiment_log(FOLDER)), list(CELLS), None).rows
    fill(ledger, rows)
