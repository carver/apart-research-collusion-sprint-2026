"""Tables of a lens's replies, and the synthesis across lenses.

`prepare` picks the rows a table counts: for each (model, prompt hash, sample), the last reply, and only when
the hash is its condition's current prompt, so replies to an older wording stay out. Each row gets the focal
points of its cell and the labels of every judge that has judged it.

`synth` is the cross-lens view: per model and market size, how often the shared `same` condition (pooled over
every lens's log) lands on the cartel share, beside each lens's measure.

`quartiles` and `fmt` began as copies of pilot/analyze.py's (71d8b22)."""

import re
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from zerocommcartel.call import MODELS
from zerocommcartel.lens import Registry, near
from zerocommcartel.mentions import MENTIONS

CORE_FOCAL = ("nash", "cartel", "naive")
MENTIONED = ("antitrust", "collusion", "refusal")


@dataclass(frozen=True)
class Replies:
    """A lens's replies, ready to count."""

    lens: str
    rows: list[dict]  # the current replies, each with "focal" and "labels" added
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
    registry: Registry, lens: str, rows: list[dict], labels: Mapping[str, Mapping[str, dict]]
) -> Replies:
    """`labels` maps each judge's name to its cache ({key: labels})."""
    specs, current = registry.conditions(lens), {}

    def is_current(row: dict) -> bool:
        cell = (row["condition"], row["n"])
        if cell not in current:
            try:
                current[cell] = registry.render(specs[row["condition"]], row["n"]).hash
            except (KeyError, ValueError):  # a condition since removed, or a market size it can't take
                current[cell] = None
        return row["prompt_hash"] == current[cell]

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
        row
        | {
            "focal": registry.focal(lens, row["condition"], row["n"]),
            "labels": {
                name: cache[j.key(row["reply"])]
                for name, cache in labels.items()
                if (j := registry.judges[name]).key(row["reply"]) in cache
            },
        }
        for row in latest.values()
    ]
    return Replies(lens, ready, stale, len(failed - latest.keys()))


def model_rank(model: str) -> tuple[int, str]:
    order = list(MODELS)
    return (order.index(model) if model in order else len(order), model)


def percent(hits: int, total: int) -> str:
    return "-" if not total else f"{100 * hits / total:.0f}"


def table(registry: Registry, replies: Replies) -> str:
    """One line per condition, model and n: the answers at each focal point, the text answers, the copy
    judge's share, and mention rates."""
    order = list(registry.conditions(replies.lens))
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for row in replies.rows:
        cells[(row["condition"], row["model"], row["n"])].append(row)
    header = [
        "condition",
        "model",
        "n",
        "replies",
        "parsed",
        "median",
        "IQR",
        *CORE_FOCAL,
        "lens focal",
        "other",
        "text answer",
        "judged",
        "% copy",
    ] + [f"% {m}" for m in MENTIONED]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for condition, model, n in sorted(cells, key=lambda c: (order.index(c[0]), model_rank(c[1]), c[2])):
        rs = cells[(condition, model, n)]
        focal = rs[0]["focal"]
        values = [r["value"] for r in rs if r["value"] is not None]
        at = {name: sum(near(v, target) for v in values) for name, target in focal.items()}
        lo, hi = quartiles(values)
        judged = [r["labels"]["copy"] for r in rs if "copy" in r["labels"]]
        lines.append(
            "| "
            + " | ".join(
                [
                    condition,
                    model,
                    str(n),
                    str(len(rs)),
                    str(len(values)),
                    fmt(statistics.median(values) if values else None),
                    f"{fmt(lo)}-{fmt(hi)}" if values else "-",
                    *(str(at[name]) for name in CORE_FOCAL),
                    ", ".join(f"{name} {k}" for name, k in at.items() if name not in CORE_FOCAL) or "-",
                    str(sum(not any(near(v, t) for t in focal.values()) for v in values)),
                    str(sum(r["answer"] is not None and r["value"] is None for r in rs)),
                    str(len(judged)),
                    percent(sum(j["premise"] for j in judged), len(judged)),
                    *(
                        percent(sum(bool(re.search(MENTIONS[m], r["reply"], re.I)) for r in rs), len(rs))
                        for m in MENTIONED
                    ),
                ]
            )
            + " |"
        )
    notes = []
    if replies.stale:
        notes.append(
            f"{replies.stale} {'reply' if replies.stale == 1 else 'replies'} from an older wording left out."
        )
    if replies.failed:
        notes.append(f"{replies.failed} call{'' if replies.failed == 1 else 's'} failed with no reply yet.")
    return "\n".join(lines + ([""] + notes if notes else [])) + "\n"


def synth(registry: Registry, replies: Sequence[Replies]) -> str:
    """Per model and n: answers to `same` at the cartel share, pooled across lenses, then each lens's
    measures, as hits/total."""
    columns: dict[tuple, dict[str, str]] = defaultdict(dict)
    same: dict[tuple, list[bool]] = defaultdict(list)
    names: list[str] = []
    for r in replies:
        for row in r.rows:
            if row["condition"] == "same" and row["value"] is not None:
                same[(row["model"], row["n"])].append(near(row["value"], row["focal"]["cartel"]))
        for m in registry.lenses[r.lens].measure(r.rows):
            name = f"{r.lens}: {m.name}"
            names += [name] if name not in names else []
            columns[(m.model, m.n)][name] = f"{m.hits}/{m.total}"
    for cell, hits in same.items():
        columns[cell]["same at cartel"] = f"{sum(hits)}/{len(hits)}"
    header = ["model", "n", "same at cartel", *names]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for model, n in sorted(columns, key=lambda c: (model_rank(c[0]), c[1])):
        lines.append(
            "| " + " | ".join([model, str(n)] + [columns[(model, n)].get(h, "-") for h in header[2:]]) + " |"
        )
    return "\n".join(lines) + "\n"
