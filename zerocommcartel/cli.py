"""zcc: run and tabulate the criteria's conditions.

    uv run zcc list                                   # each criterion and its conditions
    uv run zcc show consistent same 2                 # one condition's system prompt and prompt, n = 2
    uv run zcc run consistent --models haiku --samples 2 --out /tmp/smoke.jsonl
    uv run zcc judge consistent                       # the copy judge labels each reply (cached)
    uv run zcc table consistent                       # a markdown table per condition, model and n
    uv run zcc table consistent --conditions same --models haiku  # only those rows
    uv run zcc synth                                  # the measures beside same's cartel and deliberate rates
    uv run zcc hashes                                 # prompt hashes and judge keys, to diff across a change

`run` appends to logs/<criterion>/results.jsonl unless --out names another file. It skips the replies it
already has, so raising --samples adds samples and a rerun retries failures. The baseline (base, diff, same)
is one prompt in every criterion, so without --out or --log a command also reads the other criteria's logs
for their baseline replies: `run` skips those samples, `table` and `synth` count them, and `judge` labels
the ones no other criterion's cache has. Smoke tests use --out, which stands alone, and the Claude
subscription (haiku, sonnet, opus); OpenRouter models need OPENROUTER_API_KEY.
"""

import argparse
import contextlib
import sys
from pathlib import Path

from zerocommcartel import logs
from zerocommcartel.call import MODELS, NAMES
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criterion import BASELINE, Registry
from zerocommcartel.judge import Judge, label, load_labels
from zerocommcartel.prompt import MODEL
from zerocommcartel.run import done_keys, plan, run
from zerocommcartel.table import Replies, prepare, synth, table

NS = [2, 4]  # the market sizes run and hashes cover by default


def sources(registry: Registry, criterion: str, given: str | None) -> tuple[Path, list[Path]]:
    """The log a command on `criterion` reads or appends to, and the logs whose baseline rows (base, diff,
    same) it counts beside that log's own. A file named by --log or --out (a smoke test, say) stands alone.
    Otherwise it's the criterion's own log, with every other criterion's beside it: the baseline renders one
    prompt in every criterion, so each of its samples runs once and counts everywhere."""
    if given:
        return Path(given), []
    return logs.log_path(criterion), [
        logs.log_path(other) for other in registry.criteria if other != criterion
    ]


def counted_rows(log: Path, shared: list[Path]) -> list[dict]:
    """The shared logs' baseline rows, then the log's own. Where two logs hold one (model, prompt hash,
    sample), the last row wins, so the criterion's own reply does."""
    borrowed = [row for path in shared for row in logs.load_rows(path) if row.get("condition") in BASELINE]
    return borrowed + logs.load_rows(log)


def labels_beside(judge: Judge, paths: list[Path]) -> dict[str, dict]:
    """The judge's labels from the caches beside each of the logs."""
    return {
        key: found
        for path in paths
        for key, found in load_labels(judge, logs.judge_path(path, judge.name)).items()
    }


def replies(
    registry: Registry,
    criterion: str,
    given: str | None,
    conditions: list[str] | None = None,
    models: list[str] | None = None,
) -> Replies:
    """The criterion's replies, only those of `conditions` and `models` when either is given."""
    log, shared = sources(registry, criterion, given)
    labels = {name: labels_beside(judge, [*shared, log]) for name, judge in registry.judges.items()}
    rows = [
        row
        for row in counted_rows(log, shared)
        if (conditions is None or row["condition"] in conditions)
        and (models is None or row["model"] in models)
    ]
    return prepare(registry, criterion, rows, labels)


def cmd_list(registry: Registry, args):
    for name, criterion in registry.criteria.items():
        print(f"{name}: {criterion.question}")
        for cond, spec in registry.conditions(name).items():
            parts = [f"{slot}={level}" for slot, level in spec.levels.items()]
            print(f"  {cond:<14} {' '.join([*parts, f'ask={spec.ask}', f'game={spec.game.name}'])}")


def cmd_show(registry: Registry, args):
    try:
        name = NAMES[args.model] if args.model else MODEL
        p = registry.render(registry.condition(args.criterion, args.condition), args.n, name)
    except ValueError as e:
        sys.exit(str(e))
    print(f"[system] {p.system}\n\n{p.user}")


def cmd_run(registry: Registry, args):
    out, shared = sources(registry, args.criterion, args.out)
    conditions = args.conditions or list(registry.conditions(args.criterion))
    try:
        tasks = plan(
            registry,
            args.criterion,
            conditions,
            args.models,
            args.ns,
            args.samples,
            done_keys(counted_rows(out, shared)),
        )
    except ValueError as e:
        sys.exit(f"no calls made: {e}")
    run(tasks, out, workers=args.workers)


def cmd_judge(registry: Registry, args):
    """Label the replies the criterion's tables count, the shared baseline's among them, into the cache beside
    its log; a reply already labelled beside another criterion's log is left as it is."""
    log, shared = sources(registry, args.criterion, args.log)
    texts = [row["reply"] for row in replies(registry, args.criterion, args.log).rows]
    for name in args.judges:
        judge = registry.judges[name]
        judged, failed, cached = label(
            judge, texts, logs.judge_path(log, name), known=labels_beside(judge, shared).keys()
        )
        print(f"{name}: judged {judged}, {len(failed)} failed, {cached} already cached")
        for line in failed:
            print(f"  failed {line}")


def cmd_table(registry: Registry, args):
    try:
        for name in args.conditions or []:
            registry.condition(args.criterion, name)
    except ValueError as e:
        sys.exit(str(e))
    found = replies(registry, args.criterion, args.log, args.conditions, args.models)
    if (args.conditions or args.models) and not found.rows:
        print("No replies match the conditions and models asked for.")
        return
    print(table(registry, found), end="")


def cmd_synth(registry: Registry, args):
    print(synth(registry, [replies(registry, criterion, None) for criterion in registry.criteria]), end="")


def cmd_hashes(registry: Registry, args):
    """A line per prompt (criterion, condition, n, hash) and per judge (its key for an empty reply, which
    moves whenever its cached labels go stale). Diff it across a shared-core change to see which logs it
    ages."""
    for name in registry.criteria:
        for cond, spec in registry.conditions(name).items():
            for n in args.ns:
                with contextlib.suppress(ValueError):  # a market size the condition's game can't take
                    print(f"{name} {cond} {n} {registry.render(spec, n).hash}")
    for name, judge in registry.judges.items():
        print(f"judge {name} {judge.key('')}")


def main(argv=None, registry: Registry = REGISTRY):
    p = argparse.ArgumentParser(
        prog="zcc", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    criteria = list(registry.criteria)
    sub.add_parser("list", help="each criterion and its conditions")
    s = sub.add_parser("show", help="print one condition's prompt")
    s.add_argument("criterion", choices=criteria)
    s.add_argument("condition", help="one of the criterion's conditions, as `zcc list` names them")
    s.add_argument("n", type=int, help="the number of firms in the market, such as 2, 3 or 4")
    s.add_argument("--model", choices=list(MODELS), help="the model a prompt names, if it names one")
    s = sub.add_parser("run", help="ask the models, appending to the criterion's log")
    s.add_argument("criterion", choices=criteria)
    s.add_argument("--conditions", nargs="+", help="default: all of the criterion's conditions")
    s.add_argument("--models", nargs="+", default=["haiku", "sonnet", "opus"])
    s.add_argument(
        "--ns", nargs="+", type=int, default=NS, help="numbers of firms; each game says which it takes"
    )
    s.add_argument("--samples", type=int, default=3)
    s.add_argument("--workers", type=int, default=40)
    s.add_argument("--out", help="default: logs/<criterion>/results.jsonl")
    s = sub.add_parser("judge", help="label the criterion's replies with judges (cached beside the log)")
    s.add_argument("criterion", choices=criteria)
    s.add_argument("--judges", nargs="+", default=["copy"], choices=list(registry.judges))
    s.add_argument("--log", help="default: logs/<criterion>/results.jsonl")
    s = sub.add_parser("table", help="a markdown table of the criterion's replies")
    s.add_argument("criterion", choices=criteria)
    s.add_argument("--log", help="default: logs/<criterion>/results.jsonl")
    s.add_argument("--conditions", nargs="+", help="only these conditions' rows; default: all")
    s.add_argument("--models", nargs="+", choices=list(MODELS), help="only these models' rows; default: all")
    sub.add_parser(
        "synth", help="every criterion's measures beside the same-prompt cartel and deliberate rates"
    )
    s = sub.add_parser("hashes", help="prompt hashes and judge keys; diff them across a shared-core change")
    s.add_argument("--ns", nargs="+", type=int, default=NS, help="numbers of firms")
    args = p.parse_args(argv)
    {
        "list": cmd_list,
        "show": cmd_show,
        "run": cmd_run,
        "judge": cmd_judge,
        "table": cmd_table,
        "synth": cmd_synth,
        "hashes": cmd_hashes,
    }[args.cmd](registry, args)
