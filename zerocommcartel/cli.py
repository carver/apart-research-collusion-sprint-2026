"""zcc: run and tabulate the criteria's conditions.

    uv run zcc list                                   # each criterion and its conditions
    uv run zcc show consistent same 2                 # one condition's system prompt and prompt, n = 2
    uv run zcc run consistent --models haiku --samples 2 --out /tmp/smoke.jsonl
    uv run zcc judge consistent                       # the copy judge labels each reply (cached)
    uv run zcc table consistent                       # a markdown table per condition, model and n
    uv run zcc synth                                  # each criterion's measures beside same's cartel rate
    uv run zcc hashes                                 # prompt hashes and judge keys, to diff across a change

`run` appends to logs/<criterion>/results.jsonl unless --out names another file. It skips the replies it
already has, so raising --samples adds samples and a rerun retries failures. Smoke tests use --out and the
Claude subscription (haiku, sonnet, opus); OpenRouter models need OPENROUTER_API_KEY.
"""

import argparse
import contextlib
import sys
from pathlib import Path

from zerocommcartel import logs
from zerocommcartel.call import MODELS, NAMES
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criterion import Registry
from zerocommcartel.judge import label, load_labels
from zerocommcartel.prompt import MODEL
from zerocommcartel.run import done_keys, plan, run
from zerocommcartel.table import Replies, prepare, synth, table

NS = [2, 4]  # the market sizes run and hashes cover by default


def replies(registry: Registry, criterion: str, log: Path) -> Replies:
    labels = {name: load_labels(j, logs.judge_path(log, name)) for name, j in registry.judges.items()}
    return prepare(registry, criterion, logs.load_rows(log), labels)


def cmd_list(registry: Registry, args):
    for name, criterion in registry.criteria.items():
        print(f"{name}: {criterion.question}")
        for cond, spec in registry.conditions(name).items():
            parts = [f"{slot}={level}" for slot, level in spec.levels.items()]
            print(f"  {cond:<14} {' '.join([*parts, f'ask={spec.ask}', f'game={spec.game.name}'])}")


def chosen_log(criterion: str, given: str | None) -> Path:
    """The log a command reads or appends to: the one given (--log, --out), else the criterion's own."""
    return Path(given) if given else logs.log_path(criterion)


def cmd_show(registry: Registry, args):
    try:
        name = NAMES[args.model] if args.model else MODEL
        p = registry.render(registry.condition(args.criterion, args.condition), args.n, name)
    except ValueError as e:
        sys.exit(str(e))
    print(f"[system] {p.system}\n\n{p.user}")


def cmd_run(registry: Registry, args):
    out = chosen_log(args.criterion, args.out)
    conditions = args.conditions or list(registry.conditions(args.criterion))
    try:
        tasks = plan(
            registry,
            args.criterion,
            conditions,
            args.models,
            args.ns,
            args.samples,
            done_keys(logs.load_rows(out)),
        )
    except ValueError as e:
        sys.exit(f"no calls made: {e}")
    run(tasks, out, workers=args.workers)


def cmd_judge(registry: Registry, args):
    log = chosen_log(args.criterion, args.log)
    rows = [r for r in logs.load_rows(log) if r.get("reply")]
    for name in args.judges:
        judged, failed, cached = label(
            registry.judges[name], [r["reply"] for r in rows], logs.judge_path(log, name)
        )
        print(f"{name}: judged {judged}, {len(failed)} failed, {cached} already cached")
        for line in failed:
            print(f"  failed {line}")


def cmd_table(registry: Registry, args):
    print(table(registry, replies(registry, args.criterion, chosen_log(args.criterion, args.log))), end="")


def cmd_synth(registry: Registry, args):
    print(
        synth(
            registry,
            [replies(registry, criterion, logs.log_path(criterion)) for criterion in registry.criteria],
        ),
        end="",
    )


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
    s.add_argument("condition")
    s.add_argument("n", type=int)
    s.add_argument("--model", choices=list(MODELS), help="the model a prompt names, if it names one")
    s = sub.add_parser("run", help="ask the models, appending to the criterion's log")
    s.add_argument("criterion", choices=criteria)
    s.add_argument("--conditions", nargs="+", help="default: all of the criterion's conditions")
    s.add_argument("--models", nargs="+", default=["haiku", "sonnet", "opus"])
    s.add_argument(
        "--ns", nargs="+", type=int, default=NS, help="market sizes; each game says which it takes"
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
    sub.add_parser("synth", help="every criterion's measures beside the same-prompt cartel rate")
    s = sub.add_parser("hashes", help="prompt hashes and judge keys; diff them across a shared-core change")
    s.add_argument("--ns", nargs="+", type=int, default=NS, help="market sizes")
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
