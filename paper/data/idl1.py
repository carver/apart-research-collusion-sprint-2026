"""The identity lever (IDL-1, #41): its figure and its table of tests, from the rows its experiment logged.

The figure draws only the comparisons that pass `zerocommcartel.criteria.communal.idl1.verdicts`, whose
docstring gives the rule and whose constants its numbers. Under its title, one panel per model with a passing
comparison; a bar per comparison, the identity's share at the cartel share minus its reference's, from the
replies its verdict used, with Newcombe's 95% interval as a whisker, labelled in three columns: the start
(Context), the reference (Baseline) and the identity (Experiment). A bar that ends at 0% or 100% and is no
longer than CAP is marked * past its whisker, since the floor or the ceiling may have cut it short. The table
lists every test, then the sanity checks (one owner over both firms against the bare start), which the
correction leaves out. The ledger also counts, for the prose, the bars that refusals explain (`set_aside`)
and those that hold without them, and the refusals behind the bars, with those giving the law and harm."""

from typing import Any, NamedTuple

from matplotlib.ticker import FuncFormatter
from matplotlib.transforms import blended_transform_factory, offset_copy

from paper.data import source
from paper.ledger import Ledger
from zerocommcartel import cli, logs
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.communal.identity import CELLS, IDENTITIES, STARTS
from zerocommcartel.criteria.communal.idl1 import (
    FIRST,
    FOLDER,
    SCREEN,
    Comparison,
    Q,
    newcombe,
    refusals_behind,
    sanity_checks,
    set_aside,
)
from zerocommcartel.criteria.communal.judge import REFUSAL, outcome
from zerocommcartel.judge import load_labels

MODELS = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus", "astra": "GPT-6 Astra", "glm": "GLM-5.3"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e0e0e0"
TOWARD, AWAY = "#2a78d6", "#e34948"  # dataviz's diverging poles: toward the cartel share, away from it
START_LABELS = {
    "unsaid": "no repeat mentioned",
    "single": "one-round game",
    "opennash": "competition history",  # eight quarters at Nash before this one
    "open": "repeated game",
    "mirror": "same prompt",
    "goodwill": "collusion history",  # eight quarters at the cartel share before this one
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
TITLE = "Conscience: Effect on Cartel Choice %"
COLUMNS = {"Context": 0.01, "Baseline": 0.16, "Experiment": 0.355}  # heads, at their left edge in the figure
BARS = (0.56, 0.98)  # where the panels start and end, in the figure: the columns sit to their left
PANEL_GAP = 0.35  # between panels, as a share of a panel's height: room for each model's name
HEAD_GAP, TITLE_GAP = 14, 30  # points above the first panel's top: past its model's name, then past the heads
STAR_GAP = 0.03  # how far past its whisker's far end the * sits, in the axis's units
HOW = "IDL-1's passing comparisons, from logs/communal/idl1/results.jsonl (communal.idl1.verdicts)"


def difference(c: Comparison) -> float:
    return c.hits / c.n - c.reference_hits / c.reference_n


def capped(c: Comparison) -> bool:
    """Whether the bar ends at 0% or 100% and is no longer than CAP: the floor or the ceiling may have
    stopped it."""
    return c.hits in (0, c.n) and abs(difference(c)) <= CAP


def arms(c: Comparison) -> str:
    """The comparison as the tests table names it: the identity against its reference."""
    return f"{ARM_LABELS[CELLS[c.target].identity]} vs {ARM_LABELS[CELLS[c.reference].identity]}"


def columns(c: Comparison) -> dict[str, str]:
    """The comparison's label in each of COLUMNS: its start, its reference's identity and its own."""
    return {
        "Context": START_LABELS[c.start],
        "Baseline": ARM_LABELS[CELLS[c.reference].identity],
        "Experiment": ARM_LABELS[CELLS[c.target].identity],
    }


class FigureData(NamedTuple):
    panels: dict[str, list[Comparison]]  # model: its passing comparisons, in drawing order


def draw(ax: Any, data: FigureData) -> None:
    """The title and the column heads, then one panel per model, stacked; replaces the one axes `figure()`
    gives with its own grid."""
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
    fig.subplots_adjust(left=BARS[0], right=BARS[1], hspace=PANEL_GAP)
    for panel, model in zip((row[0] for row in axes), models, strict=True):
        found = data.panels[model]
        beside = blended_transform_factory(fig.transFigure, panel.transData)
        for y, c in enumerate(found):
            d = difference(c)
            low, high = newcombe(c.hits, c.n, c.reference_hits, c.reference_n)
            panel.barh(y, d, height=0.6, color=TOWARD if d > 0 else AWAY, edgecolor="white", linewidth=0.8)
            panel.errorbar(
                d, y, xerr=[[d - low], [high - d]], fmt="none", ecolor=INK, elinewidth=0.7, capsize=2
            )
            if capped(c):  # past the whisker's far end, on the bar's side of zero
                x, align = (low - STAR_GAP, "right") if d < 0 else (high + STAR_GAP, "left")
                panel.text(x, y, "*", ha=align, va="center", fontsize=8, color=INK)
            labels = columns(c)
            for head, x in COLUMNS.items():
                panel.text(
                    x, y, labels[head], transform=beside, ha="left", va="center", fontsize=6.5, color=INK
                )
        panel.axvline(0, color=MUTED, linewidth=0.7)
        panel.set_yticks([])
        panel.set_ylim(len(found) - 0.5, -0.5)
        panel.set_xlim(-1.05, 1.05)
        panel.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x * 100:+.0f}" if x else "0"))
        panel.grid(axis="x", color=GRID, linewidth=0.6)
        panel.set_axisbelow(True)
        panel.tick_params(axis="both", length=0, labelsize=6.5)
        for side in ("top", "right", "left"):
            panel.spines[side].set_visible(False)
        panel.set_title(MODELS.get(model, model), fontsize=8, color=INK, loc="left")
    # in points above the first panel, so a short figure keeps the title clear of the heads
    over = blended_transform_factory(fig.transFigure, axes[0][0].transAxes)
    heads = offset_copy(over, fig=fig, y=HEAD_GAP, units="points")
    for head, x in COLUMNS.items():
        fig.text(
            x, 1, head, transform=heads, ha="left", va="bottom", fontsize=7, color=INK, fontweight="bold"
        )
    title = offset_copy(over, fig=fig, y=TITLE_GAP, units="points")
    fig.text(
        0.5, 1, TITLE, transform=title, ha="center", va="bottom", fontsize=9.5, color=INK, fontweight="bold"
    )
    axes[-1][0].set_xlabel("cartel share, relative to baseline (points)", fontsize=7, color=MUTED)


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


def fill(ledger: Ledger, rows: list[dict], labels: dict[str, dict]) -> None:
    pairs = set_aside(rows, labels)  # raises if the refusal judge hasn't labelled a reply a test needs
    found = [c for c, _ in pairs]
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
    named = [m for m in MODELS if m in models] + [m for m in models if m not in MODELS]  # MODELS' order
    ledger.value(
        "idl1.models",
        " ".join(named),
        how="the models whose every cell has its first stage, so in the family",
    )
    ledger.value("idl1.pass", len(passing), how=f"comparisons that pass (q < {Q:g})")
    ledger.value(
        "idl1.pass.which",
        " ".join(sorted(f"{c.model}:{c.target}" for c in passing)),
        how="those comparisons, as model:target, for the claims",
    )
    ledger.value(
        "idl1.aside",
        sum(c.passes and not a.passes for c, a in pairs),
        how="passing comparisons that miss with refusals set aside (communal.idl1.set_aside)",
    )
    held = sorted(f"{c.model}:{c.target}" for c, a in pairs if c.passes and a.passes)
    ledger.value(
        "idl1.aside.held", len(held), how="passing comparisons that still pass with refusals set aside"
    )
    ledger.value(
        "idl1.aside.held.which", " ".join(held), how="those comparisons, as model:target, for a claim"
    )
    refused, law, harm = refusals_behind(passing, rows, labels)
    ledger.value(
        "idl1.refusals",
        refused,
        how="refusals in the replies behind the passing bars, each model, cell and stage once",
    )
    ledger.value("idl1.refusals.law", law, how="those refusals that give the law as a reason")
    ledger.value(
        "idl1.refusals.harm", harm, how="those refusals that give harm as a reason, with the law or without"
    )
    for model in models:
        read = [row for row in rows if row["model"] == model and REFUSAL.key(row["reply"]) in labels]
        if not read:  # pooled() refuses no rows; the key goes missing, which the build reports
            continue
        ledger.pooled(
            f"idl1.{model}.refusals",
            read,
            lambda row: outcome(row, labels) == "refusal",
            how="refusals / the model's replies the refusal judge read, every cell and stage",
        )
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
        "idl1.sentence.price",
        IDENTITIES["price"],
        how="the price sentence, verbatim, for the caption (communal.identity.IDENTITIES)",
    )
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
    log = logs.experiment_log(FOLDER)
    rows = cli.replies(REGISTRY, "communal", str(log), list(CELLS), None).rows
    fill(ledger, rows, load_labels(REFUSAL, logs.judge_path(log, REFUSAL.name)))
