"""zcc: run and tabulate the lenses' conditions.

    uv run zcc list                                   # each lens and its conditions
    uv run zcc show consistent same 2                 # one condition's system prompt and prompt, n = 2
    uv run zcc run consistent --models haiku --samples 2 --out /tmp/smoke.jsonl
    uv run zcc judge consistent                       # the copy judge labels each reply (cached)
    uv run zcc table consistent                       # a markdown table per condition, model and n
    uv run zcc synth                                  # each lens's measures beside same's cartel rate

`run` appends to logs/<lens>/results.jsonl unless --out names another file. It skips the replies it already
has, so raising --samples adds samples and a rerun retries failures. Smoke tests use --out and the Claude
subscription (haiku, sonnet, opus); OpenRouter models need OPENROUTER_API_KEY.
"""

import argparse
import sys
from pathlib import Path

from zerocommcartel import logs
from zerocommcartel.judge import label, load_labels
from zerocommcartel.lens import Registry
from zerocommcartel.lenses import REGISTRY
from zerocommcartel.run import done_keys, plan, run
from zerocommcartel.table import Replies, prepare, synth, table


def replies(registry: Registry, lens: str, log: Path) -> Replies:
    labels = {name: load_labels(j, logs.judge_path(log, name)) for name, j in registry.judges.items()}
    return prepare(registry, lens, logs.load_rows(log), labels)


def cmd_list(registry: Registry, args):
    for name, lens in registry.lenses.items():
        print(f"{name}: {lens.question}")
        for cond, spec in registry.conditions(name).items():
            parts = [f"{slot}={level}" for slot, level in spec.levels.items()]
            print(f"  {cond:<14} {' '.join([*parts, f'ask={spec.ask}', f'game={spec.game.name}'])}")


def cmd_show(registry: Registry, args):
    specs = registry.conditions(args.lens)
    if args.condition not in specs:
        sys.exit(f"lens {args.lens!r} has no condition {args.condition!r}; it has {', '.join(specs)}")
    try:
        p = registry.render(specs[args.condition], args.n)
    except ValueError as e:
        sys.exit(str(e))
    print(f"[system] {p.system}\n\n{p.user}")


def cmd_run(registry: Registry, args):
    out = Path(args.out) if args.out else logs.log_path(args.lens)
    conditions = args.conditions or list(registry.conditions(args.lens))
    try:
        tasks = plan(
            registry,
            args.lens,
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
    log = Path(args.log) if args.log else logs.log_path(args.lens)
    rows = [r for r in logs.load_rows(log) if r.get("reply")]
    for name in args.judges:
        judged, failed, cached = label(
            registry.judges[name], [r["reply"] for r in rows], logs.judge_path(log, name)
        )
        print(f"{name}: judged {judged}, {len(failed)} failed, {cached} already cached")
        for line in failed:
            print(f"  failed {line}")


def cmd_table(registry: Registry, args):
    log = Path(args.log) if args.log else logs.log_path(args.lens)
    print(table(registry, replies(registry, args.lens, log)), end="")


def cmd_synth(registry: Registry, args):
    print(synth(registry, [replies(registry, lens, logs.log_path(lens)) for lens in registry.lenses]), end="")


def main(argv=None, registry: Registry = REGISTRY):
    p = argparse.ArgumentParser(
        prog="zcc", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    lenses = list(registry.lenses)
    sub.add_parser("list", help="each lens and its conditions")
    s = sub.add_parser("show", help="print one condition's prompt")
    s.add_argument("lens", choices=lenses)
    s.add_argument("condition")
    s.add_argument("n", type=int)
    s = sub.add_parser("run", help="ask the models, appending to the lens's log")
    s.add_argument("lens", choices=lenses)
    s.add_argument("--conditions", nargs="+", help="default: all of the lens's conditions")
    s.add_argument("--models", nargs="+", default=["haiku", "sonnet", "opus"])
    s.add_argument(
        "--ns", nargs="+", type=int, default=[2, 4], help="market sizes; each game says which it takes"
    )
    s.add_argument("--samples", type=int, default=3)
    s.add_argument("--workers", type=int, default=40)
    s.add_argument("--out", help="default: logs/<lens>/results.jsonl")
    s = sub.add_parser("judge", help="label the lens's replies with judges (cached beside the log)")
    s.add_argument("lens", choices=lenses)
    s.add_argument("--judges", nargs="+", default=["copy"], choices=list(registry.judges))
    s.add_argument("--log", help="default: logs/<lens>/results.jsonl")
    s = sub.add_parser("table", help="a markdown table of the lens's replies")
    s.add_argument("lens", choices=lenses)
    s.add_argument("--log", help="default: logs/<lens>/results.jsonl")
    sub.add_parser("synth", help="every lens's measures beside the same-prompt cartel rate")
    args = p.parse_args(argv)
    {
        "list": cmd_list,
        "show": cmd_show,
        "run": cmd_run,
        "judge": cmd_judge,
        "table": cmd_table,
        "synth": cmd_synth,
    }[args.cmd](registry, args)
