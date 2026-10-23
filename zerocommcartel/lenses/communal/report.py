"""The communal lens's report: the mirror-stated defection over the pilot's `same` replies and the lens's own,
and the rule judge's labels for each of the lens's conditions.

    uv run python -m zerocommcartel.lenses.communal.report           # the lens's log, logs/communal/
    uv run python -m zerocommcartel.lenses.communal.report --judge   # label the pilot's `same` replies first
    uv run python -m zerocommcartel.lenses.communal.report --log /tmp/smoke.jsonl

The lens's own replies get their labels from `zcc judge communal --judges copy rule`. The pilot's `same`
replies (logs/pilot/, frozen) share the lens's `same` prompt and carry the pilot's copy labels. Their rule
labels go in the rule judge's cache beside the lens's log, since the pilot's folder takes no new files; the
judge's keys hash the reply alone, so one cache serves both."""

import argparse
from collections import defaultdict
from collections.abc import Callable, Mapping
from pathlib import Path

from zerocommcartel import logs
from zerocommcartel.judge import COPY, Judge, claude_call, label, load_labels
from zerocommcartel.lens import Registry, near
from zerocommcartel.lenses import REGISTRY
from zerocommcartel.lenses.communal.judge import OBJECTIVES, ORDERS, RULE
from zerocommcartel.lenses.communal.measures import states_the_mirror
from zerocommcartel.table import Replies, markdown, model_rank, prepare

PILOT_LOG = logs.LOGS / "pilot" / "probe-results.jsonl"


def lens_replies(registry: Registry, log: Path) -> Replies:
    """The lens's replies in `log`, with the labels of every judge whose cache is beside it."""
    labels = {name: load_labels(judge, logs.judge_path(log, name)) for name, judge in registry.judges.items()}
    return prepare(registry, "communal", logs.load_rows(log), labels)


def _pilot_same_rows(pilot_log: Path) -> list[dict]:
    """The pilot's Cournot `same` rows, as rows of the lens's log."""
    return [
        {**row, "lens": "communal", "condition": "same"}
        for row in logs.load_rows(pilot_log)
        if row.get("game") == "cournot" and row.get("arm") == "same"
    ]


def pilot_same(registry: Registry, pilot_log: Path, rule_cache: Path) -> Replies:
    """The pilot's Cournot `same` replies, with the pilot's copy labels (beside its log) and the rule labels
    in `rule_cache`."""
    labels = {
        "copy": load_labels(COPY, logs.judge_path(pilot_log, "copy")),
        "rule": load_labels(RULE, rule_cache),
    }
    return prepare(registry, "communal", _pilot_same_rows(pilot_log), labels)


def judge_pilot(
    pilot_log: Path, rule_cache: Path, call: Callable[[Judge, str], str] = claude_call
) -> tuple[int, list[str], int]:
    """Label the pilot's `same` replies with the rule judge, into `rule_cache`. Returns (judged, failures,
    cached), as `zerocommcartel.judge.label` does."""
    return label(RULE, [r["reply"] for r in _pilot_same_rows(pilot_log) if r.get("reply")], rule_cache, call)


MIRROR_HEADER = [
    "source", "model", "n", "premise", "at nash", "respond first", "at cartel", "equal first", "own", "joint",
    "both",
]  # fmt: skip


def _ruled(rows: list[dict], field: str, value: str) -> str:
    """k/m: k of the m rows the rule judge has labelled have `value` in `field`."""
    found = [r["labels"]["rule"][field] for r in rows if "rule" in r["labels"]]
    return f"{found.count(value)}/{len(found)}"


def _mirror_cells(rows: list[dict]) -> list[str]:
    premise = [r for r in rows if states_the_mirror(r)]
    nash = [r for r in premise if near(r["value"], r["focal"]["nash"])]
    cartel = [r for r in premise if near(r["value"], r["focal"]["cartel"])]
    return [
        f"{len(premise)}/{len(rows)}",
        str(len(nash)),
        _ruled(nash, "order", "respond_first"),
        str(len(cartel)),
        _ruled(cartel, "order", "equal_first"),
        *(_ruled(cartel, "objective", objective) for objective in ("own", "joint", "both")),
    ]


def mirror_table(sources: Mapping[str, Replies]) -> str:
    """Per source, model and n: the parsed `same` replies that state the copy premise, of all parsed ones; of
    those, the ones at Nash and at the cartel share. Then, as k/m of the ones the rule judge has labelled: the
    Nash answers that best-respond first, the cartel answers that set the outputs equal first, and whose
    profit the cartel answers say they serve."""
    lines = []
    for source, found in sources.items():
        cells: dict[tuple[str, int], list[dict]] = defaultdict(list)
        for r in found.rows:
            if r["condition"] == "same" and r["value"] is not None:
                cells[(r["model"], r["n"])].append(r)
        for model, n in sorted(cells, key=lambda c: (model_rank(c[0]), c[1])):
            lines.append([source, model, str(n), *_mirror_cells(cells[(model, n)])])
    return markdown(MIRROR_HEADER, lines)


RULE_HEADER = [
    "condition", "model", "n", "judged", *(o.replace("_", " ") for o in ORDERS), *OBJECTIVES, "reaction",
    "follower",
]  # fmt: skip


def _rule_cells(labels: list[dict]) -> list[str]:
    return [
        str(len(labels)),
        *(str(sum(x["order"] == o for x in labels)) for o in ORDERS),
        *(str(sum(x["objective"] == o for x in labels)) for o in OBJECTIVES),
        str(sum(x["reaction"] for x in labels)),
        str(sum(x["follower"] for x in labels)),
    ]


def rule_table(registry: Registry, found: Replies) -> str:
    """Per condition, model and n, of the replies the rule judge has labelled: how many take each order of
    operations, say they serve each objective, and treat a rival as reacting to their number."""
    order = list(registry.conditions(found.lens))
    cells: dict[tuple[str, str, int], list[dict]] = defaultdict(list)
    for r in found.rows:
        if "rule" in r["labels"]:
            cells[(r["condition"], r["model"], r["n"])].append(r["labels"]["rule"])
    keys = sorted(cells, key=lambda c: (order.index(c[0]), model_rank(c[1]), c[2]))
    return markdown(RULE_HEADER, [[c, m, str(n), *_rule_cells(cells[(c, m, n)])] for c, m, n in keys])


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m zerocommcartel.lenses.communal.report",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--log", help="the lens's log; default logs/communal/results.jsonl")
    p.add_argument("--pilot-log", default=str(PILOT_LOG), help="default: logs/pilot/probe-results.jsonl")
    p.add_argument(
        "--judge",
        action="store_true",
        help="first label the pilot's same replies with the rule judge (Haiku)",
    )
    args = p.parse_args(argv)
    log = Path(args.log) if args.log else logs.log_path("communal")
    pilot_log, cache = Path(args.pilot_log), logs.judge_path(log, "rule")
    if args.judge:
        judged, failed, cached = judge_pilot(pilot_log, cache)
        print(f"rule, pilot's same replies: judged {judged}, {len(failed)} failed, {cached} already cached")
        for line in failed:
            print(f"  failed {line}")
    lens = lens_replies(REGISTRY, log)
    print("## Mirror-stated defection on `same`\n")
    print(mirror_table({"pilot": pilot_same(REGISTRY, pilot_log, cache), "lens": lens}))
    print("## The rule judge's labels\n")
    print(rule_table(REGISTRY, lens), end="")


if __name__ == "__main__":
    main()
