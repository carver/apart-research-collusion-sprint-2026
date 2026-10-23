"""Tables of a criterion's replies, and the synthesis across criteria.

`prepare` picks the rows a table counts: for each (model, prompt hash, sample), the last reply, and only when
the hash is its condition's current prompt, so replies to an older wording stay out. Each row gets the focal
points of its cell and the labels of every judge that has judged it.

`synth` is the cross-criterion view: per model and market size, how often the shared `same` condition (pooled
over every criterion's log) lands on the cartel share, and how often deliberately (`criterion.deliberate`),
beside each criterion's measure.

`quartiles` and `fmt` began as copies of pilot/analyze.py's (71d8b22)."""

import re
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from zerocommcartel.call import MODELS, NAMES
from zerocommcartel.criterion import Registry, deliberate, near
from zerocommcartel.mentions import MENTIONS
from zerocommcartel.prompt import MODEL

CORE_FOCAL = ("nash", "cartel", "naive")
MENTIONED = ("antitrust", "collusion", "refusal")


@dataclass(frozen=True)
class Replies:
    """A criterion's replies, ready to count."""

    criterion: str
    rows: list[
        dict
    ]  # the current log rows (zerocommcartel.logs lists their fields), plus "focal" and "labels"
    stale: int  # replies to an older wording of their condition
    failed: int  # calls that failed and haven't been retried with success yet


def quartiles(xs):
    if len(xs) < 2:
        return (xs[0], xs[0]) if xs else (None, None)
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return q[0], q[2]


def fmt(x, d=1):
    return "-" if x is None else (f"{x:.{d}f}".rstrip("0").rstrip(".") if isinstance(x, float) else str(x))


def prepare(
    registry: Registry, criterion: str, rows: list[dict], labels: Mapping[str, Mapping[str, dict]]
) -> Replies:
    """`labels` maps each judge's name to its cache ({key: labels})."""
    current: dict[tuple[str, int, str], str | None] = {}

    def is_current(row: dict) -> bool:
        cell = (row["condition"], row["n"], row["model"])
        if cell not in current:
            try:
                current[cell] = registry.render(
                    registry.condition(criterion, row["condition"]), row["n"], NAMES.get(row["model"], MODEL)
                ).hash
            except ValueError:  # a condition since removed, or a market size it can't take
                current[cell] = None
        return row["prompt_hash"] == current[cell]

    def judged(reply: str) -> dict[str, dict]:
        keys = {name: registry.judges[name].key(reply) for name in labels}
        return {name: labels[name][key] for name, key in keys.items() if key in labels[name]}

    latest: dict[tuple, dict] = {}
    failed: set[tuple] = set()
    stale = 0
    for row in rows:
        key = (row["model"], row["prompt_hash"], row["sample"])
        if not is_current(row):
            stale += bool(row.get("reply"))
        elif row.get("reply"):
            latest[key] = row
        else:
            failed.add(key)
    ready = [
        row | {"focal": registry.focal(criterion, row["condition"], row["n"]), "labels": judged(row["reply"])}
        for row in latest.values()
    ]
    return Replies(criterion, ready, stale, len(failed - latest.keys()))


def model_rank(model: str) -> tuple[int, str]:
    order = list(MODELS)
    return (order.index(model) if model in order else len(order), model)


def percent(hits: int, total: int) -> str:
    return "-" if not total else f"{100 * hits / total:.0f}"


def markdown(header: list[str], lines: list[list[str]]) -> str:
    return (
        "\n".join("| " + " | ".join(cells) + " |" for cells in [header, ["---"] * len(header), *lines]) + "\n"
    )


TABLE_HEADER = [
    "condition", "model", "n", "replies", "parsed", "median", "IQR", *CORE_FOCAL, "other focal", "other",
    "text answer", "judged", "% copy", *(f"% {m}" for m in MENTIONED),
]  # fmt: skip


def cell_line(condition: str, model: str, n: int, rows: list[dict]) -> list[str]:
    """One table line: a cell's replies, counted at each of its focal points."""
    focal = rows[0]["focal"]
    values = [r["value"] for r in rows if r["value"] is not None]
    at = {name: sum(near(v, target) for v in values) for name, target in focal.items()}
    lo, hi = quartiles(values)
    copy = [r["labels"]["copy"]["premise"] for r in rows if "copy" in r["labels"]]
    mentioned = [sum(bool(re.search(MENTIONS[m], r["reply"], re.I)) for r in rows) for m in MENTIONED]
    return [
        condition,
        model,
        str(n),
        str(len(rows)),
        str(len(values)),
        fmt(statistics.median(values) if values else None),
        f"{fmt(lo)}-{fmt(hi)}" if values else "-",
        *(str(at.get(name, "-")) for name in CORE_FOCAL),
        ", ".join(f"{name} {k}" for name, k in at.items() if name not in CORE_FOCAL) or "-",
        str(sum(not any(near(v, t) for t in focal.values()) for v in values)),
        str(sum(r["answer"] is not None and r["value"] is None for r in rows)),
        str(len(copy)),
        percent(sum(copy), len(copy)),
        *(percent(k, len(rows)) for k in mentioned),
    ]


def table(registry: Registry, replies: Replies) -> str:
    """One line per condition, model and n: the answers at each focal point, the text answers, the copy
    judge's share, and mention rates. Notes after it count the replies left out and the calls still failed."""
    order = list(registry.conditions(replies.criterion))
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for row in replies.rows:
        cells[(row["condition"], row["model"], row["n"])].append(row)
    keys = sorted(cells, key=lambda c: (order.index(c[0]), model_rank(c[1]), c[2]))
    notes = []
    if replies.stale:
        notes.append(
            f"{replies.stale} {'reply' if replies.stale == 1 else 'replies'} from an older wording left out."
        )
    if replies.failed:
        notes.append(f"{replies.failed} call{'' if replies.failed == 1 else 's'} failed with no reply yet.")
    out = markdown(TABLE_HEADER, [cell_line(c, m, n, cells[(c, m, n)]) for c, m, n in keys])
    return out + "".join(f"\n{note}" for note in notes) + ("\n" if notes else "")


def synth(registry: Registry, replies: Sequence[Replies]) -> str:
    """Per model and n: answers to `same` at the cartel share, pooled across criteria, and how many of the
    judged ones are deliberate; then each criterion's measures, as hits/total."""
    columns: dict[tuple, dict[str, str]] = defaultdict(dict)
    same: dict[tuple, dict[tuple, dict]] = defaultdict(dict)  # by the log it's in: several criteria count it
    names: list[str] = []
    for r in replies:
        for row in r.rows:
            if row["condition"] == "same" and row["value"] is not None:
                same[(row["model"], row["n"])][(row["criterion"], row["prompt_hash"], row["sample"])] = row
        for m in registry.criteria[r.criterion].measure(r.rows):
            name = f"{r.criterion}: {m.name}"
            names += [name] if name not in names else []
            columns[(m.model, m.n)][name] = f"{m.hits}/{m.total}"
    for cell, replies_once in same.items():
        rows = list(replies_once.values())
        judged = [row for row in rows if "copy" in row["labels"]]
        columns[cell]["same at cartel"] = (
            f"{sum(near(r['value'], r['focal']['cartel']) for r in rows)}/{len(rows)}"
        )
        if judged:
            columns[cell]["same deliberate"] = f"{sum(map(deliberate, judged))}/{len(judged)}"
    header = ["model", "n", "same at cartel", "same deliberate", *names]
    keys = sorted(columns, key=lambda c: (model_rank(c[0]), c[1]))
    return markdown(
        header, [[model, str(n), *(columns[(model, n)].get(h, "-") for h in header[2:])] for model, n in keys]
    )
