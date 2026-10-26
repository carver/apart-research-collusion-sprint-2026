"""The capable criterion (#39): CAP-9's capability against collusion, CAP-8's history and horizon, and
CAP-10's wordings, from logs/capable/cap9, cap8 and cap10; and for Methods, the three-firm market's prompt
and its replies a cell, which also counts CPL-9's single-sentence cells, from logs/compliant/cpl9.

Every rate is the criterion's own measure (`zerocommcartel.criteria.capable.measures.at_cartel`): the replies
whose answer is exactly the cartel quantity, 20 in these three-firm markets, of all the cell's replies, so a
refusal or a missing answer counts against it. Three counts pooled across cells, for the section's prose, are
of all replies too: the answers exactly at the cartel quantity or at Nash (30), or the replies at neither,
where a reply with no answer is neither."""

from collections.abc import Iterable
from typing import Any

from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter
from matplotlib.transforms import offset_copy

from paper.data import source
from paper.data.conceptualization import replies_text
from paper.ledger import Ledger, display
from zerocommcartel import cli
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.compliant import CPL9
from zerocommcartel.criteria.compliant.report import env_levels

MODELS = {
    "opus": "Opus",
    "astra": "GPT-6 Astra",
    "glm": "GLM-5.3",
    "commandr": "Command R",
    "llama8b": "Llama 3.1 8B",
}
CAPABLE = ("opus", "astra", "glm")  # the models CAP-8 and CAP-10 ran
WEAKER = ("commandr", "llama8b")  # CAP-9's weaker models; the paper's stronger ones are CAPABLE
# dataviz's categorical slots 3, 7, 4, 5 and 6: Opus and GLM-5.3 as in the other figures
COLORS = {
    "opus": "#1baf7a",
    "astra": "#6250d6",
    "glm": "#eda100",
    "commandr": "#e87ba4",
    "llama8b": "#008300",
}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e0e0e0"

CAP9 = {"joint": "quarter_cartel_long_joint", "own": "quarter_cartel_long"}  # CAP-9's realistic market
HISTORIES = {"first": "no collusion history", "cartel": "collusion history"}  # the figure's rows, top first
HORIZONS = {
    "long": "repeated game",
    "none": "no repeat specified",
    "last": "final round",
}
WORDINGS = {  # CAP-10's arms, each after a round at 20 with an open future
    "quarter_cartel_long": "business",
    "game_cartel_long": "game words",
    "plain_own": "standard game text",
}
SINGLE = tuple(
    c for c in CPL9 if sum(level != "none" for level in env_levels(c)) <= 1
)  # CPL-9's, and its control
COUNTED = {  # the cells the paper counts in each log; one prompt in two logs is two runs, so two cells
    "cap9": tuple(CAP9.values()),
    "cap8": tuple(f"quarter_{history}_{horizon}" for history in HISTORIES for horizon in HORIZONS),
    "cap10": tuple(WORDINGS),
    "cpl9": SINGLE,
}
CPL9_LOG = "logs/compliant/cpl9/results.jsonl"
HOW = "answers exactly at the cartel quantity (20) / replies"
EITHER = "answers exactly at the cartel quantity (20) or Nash (30) / replies"
NEITHER = "replies neither at the cartel quantity (20) nor at Nash (30), or with no answer / replies"


def at_cartel(row: dict) -> bool:
    return row["value"] == row["focal"]["cartel"]


def at_cartel_or_nash(row: dict) -> bool:
    """An answer exactly at the cartel quantity or at Nash. A reply with no answer is neither."""
    return row["value"] in (row["focal"]["cartel"], row["focal"]["nash"])


def neither_cartel_nor_nash(row: dict) -> bool:
    return not at_cartel_or_nash(row)


def logged(folder: str) -> list[dict]:
    """The replies logged in logs/capable/<folder>."""
    return cli.replies(REGISTRY, "capable", f"logs/capable/{folder}/results.jsonl", None, list(MODELS)).rows


def by_cell(rows: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Replies by condition and model."""
    cells: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        cells.setdefault((row["condition"], row["model"]), []).append(row)
    return cells


def style(ax: Any) -> None:
    """The other figures' look: no ticks, a faint grid, only the bottom spine."""
    ax.tick_params(axis="both", length=0, labelsize=6.5, colors=MUTED)
    ax.set_facecolor("none")  # the page shows through
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.spines["bottom"].set_linewidth(0.7)


def draw_capability(ax: Any, dots: list[dict]) -> None:
    """One dot per model: across, its share of answers at 20 to the joint question; up, to its own decision;
    each with its 95% Wilson interval as a band. The plot is square, with one scale on both axes, so the two
    shares compare directly. Every dot sits at its shares; where dots share one across, their bands up and
    down sit side by side."""
    fig = ax.figure
    ax.set_position((0.15, 0.15, 0.8, 0.8))
    ax.set_aspect("equal")
    ax.set_xlim(-0.04, 1.04)
    ax.set_ylim(-0.04, 1.04)
    ticks = [0, 0.25, 0.5, 0.75, 1]
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.grid(color=GRID, linewidth=0.6)
    style(ax)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(MUTED)
    ax.spines["left"].set_linewidth(0.7)
    shared: dict[float, list[dict]] = {}
    for dot in dots:
        shared.setdefault(dot["joint"]["rate"], []).append(dot)
    for group in shared.values():
        for i, dot in enumerate(group):
            beside = offset_copy(ax.transData, fig=fig, x=(i - (len(group) - 1) / 2) * 3, units="points")
            joint, own, color = dot["joint"], dot["own"], COLORS[dot["model"]]
            band = {"color": color, "alpha": 0.35, "linewidth": 2.6, "solid_capstyle": "butt"}
            ax.plot([joint["lo"], joint["hi"]], [own["rate"]] * 2, **band)
            ax.plot([joint["rate"]] * 2, [own["lo"], own["hi"]], transform=beside, **band)
            ax.plot(
                joint["rate"],
                own["rate"],
                "o",
                color=color,
                markersize=6,
                markeredgecolor="white",
                markeredgewidth=0.9,
                zorder=3,
            )
    # names beside the bands, away from the plot's right edge; labels on one side kept a line apart
    sides: dict[bool, list[dict]] = {}
    for dot in dots:
        sides.setdefault(dot["joint"]["hi"] > 0.85, []).append(dot)
    for left, group in sides.items():
        last = None
        for dot in sorted(group, key=lambda d: -d["own"]["rate"]):
            y = dot["own"]["rate"] if last is None else min(dot["own"]["rate"], last - 0.05)
            last = y
            x = dot["joint"]["lo"] if left else dot["joint"]["hi"]
            at = offset_copy(ax.transData, fig=fig, x=-4 if left else 4, units="points")
            ax.text(
                x,
                y,
                MODELS[dot["model"]],
                transform=at,
                ha="right" if left else "left",
                va="center",
                fontsize=7,
                color=INK,
            )
    ax.set_title("Knowing vs choosing cartel share", fontsize=8, color=INK, fontweight="bold")
    ax.set_xlabel("finds the cartel share when asked for the joint optimum", fontsize=7, color=MUTED)
    ax.set_ylabel("produces exactly the cartel share itself", fontsize=7, color=MUTED)


def draw_history_horizon(ax: Any, cells: dict[tuple[str, str, str], dict]) -> None:
    """A 2 x 3 grid, the history down and the horizon across, with a bar per model in each cell: its share of
    answers at 20, with its 95% Wilson interval and its count. Replaces the one axes `figure()` gives with its
    own grid."""
    fig = ax.figure
    ax.remove()
    models = list(dict.fromkeys(model for model, _, _ in cells))
    grid = fig.subplots(len(HISTORIES), len(HORIZONS), sharex=True, sharey=True)
    fig.subplots_adjust(wspace=0.08, hspace=0.3)
    for r, history in enumerate(HISTORIES):
        for c, horizon in enumerate(HORIZONS):
            panel = grid[r][c]
            for i, model in enumerate(models):
                cell = cells[(model, history, horizon)]
                panel.bar(i, cell["rate"], width=0.7, color=COLORS[model], edgecolor="white", linewidth=0.8)
                panel.errorbar(
                    i,
                    cell["rate"],
                    yerr=[[cell["rate"] - cell["lo"]], [cell["hi"] - cell["rate"]]],
                    fmt="none",
                    ecolor=INK,
                    elinewidth=0.7,
                    capsize=2,
                )
                panel.text(
                    i, cell["hi"] + 0.04, str(cell["k"]), ha="center", va="bottom", fontsize=6.5, color=INK
                )
            panel.set_xlim(-0.6, len(models) - 0.4)
            panel.set_ylim(0, 1.18)
            panel.set_yticks([0, 0.5, 1])
            panel.yaxis.set_major_formatter(PercentFormatter(1.0))
            panel.set_xticks(range(len(models)), [MODELS[m] for m in models])
            panel.grid(axis="y", color=GRID, linewidth=0.6)
            style(panel)
            if r == 0:
                panel.set_title(HORIZONS[horizon], fontsize=8, color=INK, fontweight="bold")
            if c == 0:
                panel.set_ylabel(HISTORIES[history], fontsize=8, color=INK, fontweight="bold")
    fig.text(
        0.5,
        1.04,
        "Collusion needs a history and a future",
        ha="center",
        va="bottom",
        fontsize=9,
        color=INK,
        fontweight="bold",
    )
    handles = [Patch(color=COLORS[m], label=MODELS[m]) for m in models]
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=len(models),
        fontsize=7,
        frameon=False,
        handlelength=1.2,
    )
    fig.text(
        0.5,
        -0.02,
        "answers at the cartel share (20), of 30 replies a cell; whiskers: Wilson 95%",
        ha="center",
        fontsize=7,
        color=MUTED,
    )


def present(models: Iterable[str], cells: dict[tuple[str, str], list[dict]]) -> list[str]:
    """The models with replies in `cells`, in the order given."""
    seen = {model for _, model in cells}
    return [model for model in models if model in seen]


def fill_capability(ledger: Ledger, rows: list[dict]) -> None:
    """CAP-9's two questions in the realistic market: a rate per model and question, the figure, and two
    pooled counts, the stronger models' own decisions at the cartel quantity or Nash and the weaker models'
    joint answers at neither."""
    cells = by_cell(rows)
    dots = []
    for model in present(MODELS, cells):
        for ask, condition in CAP9.items():
            ledger.rate(f"cap9.{model}.{ask}", cells[(condition, model)], at_cartel, how=HOW)
        dots.append({"model": model} | {ask: ledger.entries[f"cap9.{model}.{ask}"] for ask in CAP9})
    ledger.figure("cap9-figure", draw_capability, dots, how=f"{HOW}; one dot per model", size=(2.5, 2.5))
    own = [row for model in present(CAPABLE, cells) for row in cells[(CAP9["own"], model)]]
    how = f"{EITHER}; the stronger models' own decisions, pooled"
    ledger.pooled("cap9.strong.own.cartel-or-nash", own, at_cartel_or_nash, how=how)
    joint = [row for model in present(WEAKER, cells) for row in cells[(CAP9["joint"], model)]]
    how = f"{NEITHER}; the weaker models' joint question, pooled"
    ledger.pooled("cap9.weak.joint.other", joint, neither_cartel_nor_nash, how=how)


def fill_history_horizon(ledger: Ledger, rows: list[dict]) -> None:
    """CAP-8's six cells: a rate per model and cell, the figure, and the replies it draws at the cartel
    quantity or Nash, pooled."""
    cells = by_cell(rows)
    shares, drawn = {}, []
    for model in present(CAPABLE, cells):
        for history in HISTORIES:
            for horizon in HORIZONS:
                key = f"cap8.{model}.{history}.{horizon}"
                cell = cells[(f"quarter_{history}_{horizon}", model)]
                ledger.rate(key, cell, at_cartel, how=HOW)
                shares[(model, history, horizon)] = ledger.entries[key]
                drawn += cell
    ledger.pooled(
        "cap8.cartel-or-nash", drawn, at_cartel_or_nash, how=f"{EITHER}; the figure's cells, pooled"
    )
    ledger.figure(
        "cap8-figure", draw_history_horizon, shares, how=f"{HOW}; a bar per model and cell", size=(6.5, 2.8)
    )


def fill_wordings(ledger: Ledger, rows: list[dict]) -> None:
    """CAP-10's three wordings, a rate per model and wording, and the table."""
    cells = by_cell(rows)
    lines = []
    for model in present(CAPABLE, cells):
        for condition, arm in WORDINGS.items():
            ledger.rate(
                f"cap10.{model}.{arm.replace(' ', '-')}", cells[(condition, model)], at_cartel, how=HOW
            )
        lines.append(
            [
                MODELS[model],
                *(display(ledger.entries[f"cap10.{model}.{a.replace(' ', '-')}"]) for a in WORDINGS.values()),
            ]
        )
    ledger.table("cap10-table", ["model", *WORDINGS.values()], lines, how=HOW)


def fill_cell_size(ledger: Ledger, logs: dict[str, list[dict]]) -> None:
    """The three-firm market's replies a cell, for Methods: CAP-9's two questions, CAP-8's grid, CAP-10's
    wordings and CPL-9's single sentences, each log's own (`COUNTED`). One number, or "fewest to most" when
    the cells differ."""
    sizes = [
        len(cell)
        for log, rows in logs.items()
        for (condition, _), cell in by_cell(rows).items()
        if condition in COUNTED[log]
    ]
    how = "replies a cell: CAP-9's two questions, CAP-8's grid, CAP-10's wordings, CPL-9's single sentences"
    ledger.value("capable.cells.replies", replies_text(sizes), how=how)


def rendered(condition: str) -> str:
    """A capable condition's three-firm user prompt."""
    return REGISTRY.render(REGISTRY.condition("capable", condition), 3).user


def paragraph(condition: str, starts: str) -> str:
    """The paragraph of a condition's prompt that starts with `starts`."""
    return next(p for p in rendered(condition).split("\n\n") if p.startswith(starts))


def fill_variants(ledger: Ledger) -> None:
    """How the capability lever's other cells differ from the collusive cell, `fill_prompt`'s: its horizon
    sentences and its joint question verbatim, and the two cells that leave a paragraph out. Raises
    ValueError when a left-out paragraph is still there."""
    if "Previous quarter:" in rendered("quarter_first_long") or "There will be" in rendered(
        "quarter_cartel_none"
    ):
        raise ValueError("a cell the variants table says leaves a paragraph out still has it")
    rows = [
        ["no previous quarter", "the “Previous quarter” paragraph is left out"],
        ["many more quarters to come", paragraph("quarter_cartel_long", "There will be")],
        ["this quarter is the last", paragraph("quarter_cartel_last", "There will be")],
        ["nothing said about the future", "the horizon sentence is left out"],
        ["the joint question", paragraph("quarter_cartel_long_joint", "How many tonnes")],
    ]
    ledger.table(
        "cap8-variants-table",
        ["variant", "its words in the prompt"],
        rows,
        how="the capable conditions' prompts, rendered (REGISTRY.render), paragraph by paragraph",
    )


def shown(condition: str) -> str:
    """A capable condition's three-firm prompt as `zcc show` prints it, after the command."""
    prompt = REGISTRY.render(REGISTRY.condition("capable", condition), 3)
    return f"$ bin/zcc show capable {condition} 3\n[system] {prompt.system}\n\n{prompt.user}"


def fill_prompt(ledger: Ledger) -> None:
    """The collusive cell's prompt, a quarter at the cartel quantity with many more to come, as `zcc show`
    prints it."""
    how = "the command, then the prompt as it prints it (cli.cmd_show's layout)"
    ledger.text("capable.prompt.quarter", shown(CAP9["own"]), how=how)


def fill_wording_prompts(ledger: Ledger) -> None:
    """The wording comparison's other two prompts, as `zcc show` prints them: the collusive cell in a game's
    words, and the standard game-like text."""
    how = "the command, then the prompt as it prints it (cli.cmd_show's layout)"
    for condition, arm in WORDINGS.items():
        if condition != CAP9["own"]:
            ledger.text(f"capable.prompt.{arm.replace(' ', '-')}", shown(condition), how=how)


@source("capable")
def capable(ledger: Ledger) -> None:
    logs = {folder: logged(folder) for folder in ("cap9", "cap8", "cap10")}
    fill_capability(ledger, logs["cap9"])
    fill_history_horizon(ledger, logs["cap8"])
    fill_wordings(ledger, logs["cap10"])
    logs["cpl9"] = cli.replies(REGISTRY, "compliant", CPL9_LOG, list(SINGLE), list(CAPABLE)).rows
    fill_cell_size(ledger, logs)
    fill_prompt(ledger)
    fill_variants(ledger)
    fill_wording_prompts(ledger)
