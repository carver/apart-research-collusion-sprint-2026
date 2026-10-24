"""Tables of a criterion's replies, and the synthesis across criteria.

`prepare` picks the rows a table counts: for each (model, prompt hash, sample), the last reply, and only when
the hash is its condition's current prompt, so replies to an older wording stay out. Each row gets the focal
points of its cell and the labels of every judge that has judged it, and its answer is read again from the
reply by today's parser: a log keeps the answer as the parser of its day read it.

`synth` is the cross-criterion view: per model and market size, how often the shared `same` condition (pooled
over every criterion's log) lands on the cartel share, and how often deliberately (`criterion.deliberate`),
beside each criterion's measure.

`quartiles` and `fmt` began as copies of pilot/analyze.py's (71d8b22)."""

import re
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from zerocommcartel.answer import parse
from zerocommcartel.call import MODELS, NAMES
from zerocommcartel.criterion import NEAR, Registry, deliberate, near
from zerocommcartel.mentions import MENTIONS
from zerocommcartel.prompt import MODEL, Prompt

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
    prompts: dict[tuple[str, int, str], Prompt | None] = {}

    def current_prompt(row: dict) -> Prompt | None:
        """The row's prompt, when the row's hash is its condition's current wording."""
        cell = (row["condition"], row["n"], row["model"])
        if cell not in prompts:
            try:
                prompts[cell] = registry.render(
                    registry.condition(criterion, row["condition"]), row["n"], NAMES.get(row["model"], MODEL)
                )
            except ValueError:  # a condition since removed, or a market size it can't take
                prompts[cell] = None
        prompt = prompts[cell]
        return prompt if prompt is not None and prompt.hash == row["prompt_hash"] else None

    def reread(row: dict, prompt: Prompt) -> dict:
        found = parse(row["reply"], prompt.number_key, prompt.text_keys)
        return row | {"answer": found.key, "value": found.value, "text": found.text}

    def judged(reply: str) -> dict[str, dict]:
        keys = {name: registry.judges[name].key(reply) for name in labels}
        return {name: labels[name][key] for name, key in keys.items() if key in labels[name]}

    latest: dict[tuple, dict] = {}
    failed: set[tuple] = set()
    stale = 0
    for row in rows:
        key = (row["model"], row["prompt_hash"], row["sample"])
        prompt = current_prompt(row)
        if prompt is None:
            stale += bool(row.get("reply"))
        elif row.get("reply"):
            latest[key] = reread(row, prompt)
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


SNIPPET = 200  # characters of a reply a quote shows


def at_focal(row: dict, focal: str, below: bool = False) -> bool:
    """Whether the row's parsed answer is at its focal point `focal` (within NEAR), or with `below`, more than
    NEAR below it. False when it has no parsed answer or no such focal point."""
    if row["value"] is None or focal not in row["focal"]:
        return False
    target = row["focal"][focal]
    return row["value"] < target - NEAR if below else near(row["value"], target)


def matching(
    registry: Registry, replies: Replies, measures: Sequence[tuple[str, bool]], pattern: re.Pattern | None
) -> list[dict]:
    """The replies at (or, for a measure's `below`, under) every focal point in `measures` and matching
    `pattern`, in the tables' order: condition, n, model, sample."""
    order = list(registry.conditions(replies.criterion))
    return sorted(
        (
            row
            for row in replies.rows
            if all(at_focal(row, focal, below) for focal, below in measures)
            and (pattern is None or pattern.search(row["reply"]))
        ),
        key=lambda row: (order.index(row["condition"]), row["n"], model_rank(row["model"]), row["sample"]),
    )


def quotes(rows: Sequence[dict], total: int, pattern: re.Pattern | None, full: bool, limit: int) -> str:
    """A count line, "k of total replies match", then a tagged block per row: its model, condition, market
    size, sample and parsed answer, and a snippet of the reply (or the whole reply when `full`). At most
    `limit` blocks, then a line saying how many more matched; limit 0 prints the count line alone."""
    lines = [f"{len(rows)} of {total} replies match"]
    for row in rows[:limit]:
        tag = f"{row['model']} {row['condition']} n={row['n']} sample={row['sample']}"
        lines.append(f"{tag} · {answer_label(row)}")
        if full:
            lines += ["  " + line for line in row["reply"].splitlines()]
        else:
            lines.append("  " + snippet(row["reply"], pattern))
    if limit and len(rows) > limit:
        lines.append(f"{len(rows) - limit} more match; --limit {len(rows)} shows them all")
    return "\n".join(lines) + "\n"


def answer_label(row: dict) -> str:
    """The reply's parsed answer, as its answer line's key and its number or text."""
    if row["value"] is not None:
        return f"{row['answer']} {fmt(row['value'])}"
    if row["text"]:
        return f"{row['answer']} {row['text']}"
    return "no answer"


def snippet(reply: str, pattern: re.Pattern | None) -> str:
    """About SNIPPET characters of the reply around the first match of `pattern` in the reply as written, or
    the reply's end, with whitespace collapsed. An ellipsis marks each cut."""
    found = pattern.search(reply) if pattern else None
    if found:
        middle = (found.start() + found.end()) // 2
        start = max(0, min(middle - SNIPPET // 2, len(reply) - SNIPPET))
    else:
        start = max(0, len(reply) - SNIPPET)
    end = min(len(reply), start + SNIPPET)
    shown = " ".join(reply[start:end].split())
    return ("…" if start else "") + shown + ("…" if end < len(reply) else "")


def grid(registry: Registry, replies: Replies, focal: str, below: bool = False) -> str:
    """A line per condition and n, a column per model and one pooling them ("all"): of each cell's parsed
    answers, how many are at the focal point `focal` (within NEAR), or with `below`, more than NEAR below
    it, as "k of m". A cell whose focal points don't include `focal`, or that has no parsed answer, shows
    "-"."""
    order = list(registry.conditions(replies.criterion))
    parsed = [row for row in replies.rows if row["value"] is not None]
    hits: dict[tuple[str, int], dict[str, list[bool]]] = {}
    for row in parsed:
        by_model = hits.setdefault((row["condition"], row["n"]), {})
        if focal in row["focal"]:
            by_model.setdefault(row["model"], []).append(at_focal(row, focal, below))
    models = sorted({row["model"] for row in parsed}, key=model_rank)

    def count(found: list[bool]) -> str:
        return f"{sum(found)} of {len(found)}" if found else "-"

    lines = [
        [
            condition,
            str(n),
            *(count(hits[(condition, n)].get(model, [])) for model in models),
            count([hit for found in hits[(condition, n)].values() for hit in found]),
        ]
        for condition, n in sorted(hits, key=lambda c: (order.index(c[0]), c[1]))
    ]
    return markdown(["condition", "n", *models, "all"], lines)


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
