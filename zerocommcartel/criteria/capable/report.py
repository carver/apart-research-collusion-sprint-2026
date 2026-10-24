"""The capable criterion's reports, one per experiment (experiments/ runs each one)."""

import statistics
from collections import defaultdict
from collections.abc import Callable

from zerocommcartel.criteria.capable import FRAMINGS
from zerocommcartel.game import MAX_UNITS
from zerocommcartel.table import Replies, fmt, markdown, model_rank

HISTORIES = {"cartel": "cartel round", "none": "first round", "nash": "Nash round"}  # in the reports' order
ORDER = list(HISTORIES)
HISTORY_HEADER = [
    "model", "framing", *(f"held: {h}" for h in HISTORIES.values()),
    *(f"mean: {h}" for h in HISTORIES.values()), "invalid",
]  # fmt: skip
COPY_HEADER = ["model", "framing", "history", "replies", "held", "judged", "copy: premise", "copy: acts"]
CAP1_HEADER = [
    "model", "condition", "replies", "at cartel", "invalid", "mean", "judged", "judge: optimum at cartel",
    "judge: objects", "judge: works it out",
]  # fmt: skip
CAP2_HEADER = [
    "model", "condition", "replies", "at cartel", "invalid", "mean", "judged", "rule: equal first",
    "rule: respond first", "rule: neither",
]  # fmt: skip


def valid(value: float | None) -> bool:
    """A whole number of units the market allows (EXPERIMENT_STANDARDS.md, "The default experiment")."""
    return value is not None and value == int(value) and 0 <= value <= MAX_UNITS


def values(rows: list[dict]) -> list[float]:
    return [r["value"] for r in rows if valid(r["value"])]


def mean(rows: list[dict]) -> str:
    found = values(rows)
    return fmt(statistics.mean(found) if found else None)


def grouped(replies: Replies, key: Callable[[dict], tuple]) -> dict[tuple, list[dict]]:
    """The replies by `key`, whose first part is the model, in the models' order."""
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for row in replies.rows:
        cells[key(row)].append(row)
    return dict(sorted(cells.items(), key=lambda kv: (model_rank(kv[0][0]), kv[0][1:])))


def framing_cell(row: dict) -> tuple:
    """A row's model, framing of the other firms and history, the last two as their places in FRAMINGS and
    HISTORIES, so cells sort in the reports' order."""
    framing = FRAMINGS.index(row["levels"].get("others", "no_info"))
    return (row["model"], framing, ORDER.index(row["game_params"]["history"]))


def failed_note(replies: Replies) -> str:
    return f"\n{replies.failed} calls failed with no reply yet.\n" if replies.failed else ""


def by_history(replies: Replies) -> str:
    """Per model and framing of the other firms: the answers that held (at or below the cartel quantity) of
    the replies, and the mean of the valid answers, after each history the firm was shown, and the invalid
    answers across them. The baselines fill the cartel-round columns; CAP-3 the other two."""

    cells = grouped(replies, framing_cell)
    pairs = sorted({(model, framing) for model, framing, _ in cells}, key=lambda p: (model_rank(p[0]), p[1]))
    lines = []
    for model, framing in pairs:
        by = {h: cells.get((model, framing, ORDER.index(h)), []) for h in HISTORIES}
        held = {h: sum(v <= rows[0]["focal"]["cartel"] for v in values(rows)) for h, rows in by.items()}
        lines.append(
            [
                model,
                FRAMINGS[framing],
                *(f"{held[h]}/{len(by[h])}" if by[h] else "-" for h in HISTORIES),
                *(mean(by[h]) for h in HISTORIES),
                str(sum(len(rows) - len(values(rows)) for rows in by.values())),
            ]
        )
    return markdown(HISTORY_HEADER, lines) + failed_note(replies)


def framings(replies: Replies) -> str:
    """The baselines' and CAP-3's report: `by_history`, then per cell the copy judge's labels: how many
    replies say the rivals will pick the same number because they ask the same model or reason the same way
    (premise), and how many pick their number by maximizing over one quantity all firms share (acts)."""
    lines = []
    for (model, framing, history), rows in grouped(replies, framing_cell).items():
        copy = [r["labels"]["copy"] for r in rows if "copy" in r["labels"]]
        held = sum(v <= rows[0]["focal"]["cartel"] for v in values(rows))
        lines.append(
            [
                model,
                FRAMINGS[framing],
                HISTORIES[ORDER[history]],
                str(len(rows)),
                str(held),
                str(len(copy)),
                str(sum(c["premise"] for c in copy)),
                str(sum(c["acts"] for c in copy)),
            ]
        )
    return by_history(replies) + "\n" + markdown(COPY_HEADER, lines)


def answers(rows: list[dict]) -> list[str]:
    """A cell's replies, its answers at the cartel quantity, its invalid answers and the mean of the rest."""
    found = values(rows)
    cartel = rows[0]["focal"]["cartel"]
    return [str(len(rows)), str(sum(v == cartel for v in found)), str(len(rows) - len(found)), mean(rows)]


def cap1(replies: Replies) -> str:
    """CAP-1, per model and condition: the answers, then the `working` judge's labels: the optimum its working
    reaches, an objection, and whether it works the optimum out."""
    lines = []
    for (model, condition), rows in grouped(replies, lambda r: (r["model"], r["condition"])).items():
        cartel = rows[0]["focal"]["cartel"]
        judged = [r["labels"]["working"] for r in rows if "working" in r["labels"]]
        lines.append(
            [
                model,
                condition,
                *answers(rows),
                str(len(judged)),
                str(sum(j["joint_per_firm"] == cartel for j in judged)),
                str(sum(j["declines"] for j in judged)),
                str(sum(j["derives"] for j in judged)),
            ]
        )
    return markdown(CAP1_HEADER, lines) + failed_note(replies)


def cap2(replies: Replies) -> str:
    """CAP-2, per model and condition: the answers, then the communal criterion's `rule` judge's `order`: does
    the reply set the outputs equal before maximizing (equal first), or best-respond to rivals held fixed?"""
    lines = []
    for (model, condition), rows in grouped(replies, lambda r: (r["model"], r["condition"])).items():
        orders = [r["labels"]["rule"]["order"] for r in rows if "rule" in r["labels"]]
        lines.append(
            [
                model,
                condition,
                *answers(rows),
                str(len(orders)),
                *(str(orders.count(o)) for o in ("equal_first", "respond_first", "neither")),
            ]
        )
    return markdown(CAP2_HEADER, lines) + failed_note(replies)
