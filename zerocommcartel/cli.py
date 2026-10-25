"""zcc: run and tabulate the criteria's conditions.

    bin/zcc list                                   # each criterion and its conditions
    bin/zcc list conc                              # one criterion's, by a prefix only its name has
    bin/zcc show consistent same 2                 # one condition's system prompt and prompt, n = 2
    bin/zcc run consistent --models haiku --samples 2 --out /tmp/smoke.jsonl
    bin/zcc judge consistent                       # the copy judge labels each reply (cached)
    bin/zcc table consistent                       # a markdown table per condition, model and n
    bin/zcc table consistent --conditions same --models haiku  # only those rows
    bin/zcc grid consistent --conditions same samemodel --at cartel --below nash  # condition x model
    bin/zcc replies consistent --conditions same --at nash --grep "same (AI )?model" -i  # quote replies
    bin/zcc synth                                  # the measures beside same's cartel and deliberate rates
    bin/zcc hashes                                 # prompt hashes and judge keys, to diff across a change

A command that takes a criterion takes its name or a prefix no other criterion's name shares (conc, cons).
`run` appends to logs/<criterion>/results.jsonl unless --out names another file. A criterion's replies are
that log's and its experiments' (logs/<criterion>/<id>/results.jsonl, from the scripts in experiments/). `run`
skips the replies they already have, so raising --samples adds samples and a rerun retries failures. The
baseline (base, diff, same) is one prompt in every criterion, so without --out or --log a command also reads
the other criteria's logs for their baseline replies: `run` skips those samples, and `table` and `synth`
count them. `judge` labels the replies that no cache beside another log, an experiment's or another
criterion's, has labelled. Smoke tests use --out, which stands alone, and the Claude subscription (haiku,
sonnet, opus); OpenRouter models need OPENROUTER_API_KEY.
"""

import argparse
import contextlib
import inspect
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from zerocommcartel import logs
from zerocommcartel.call import MODELS, NAMES
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criterion import BASELINE, Registry
from zerocommcartel.judge import Judge, label, load_labels
from zerocommcartel.prompt import MODEL
from zerocommcartel.run import Task, done_keys, estimate, plan, run
from zerocommcartel.table import Replies, grid, matching, prepare, quotes, synth, table

NS = [2, 4]  # the market sizes run and hashes cover by default
LOG_HELP = (
    "default: logs/<criterion>/results.jsonl, with the logs of the criterion's experiments, "
    "logs/<criterion>/<id>/results.jsonl"
)


@dataclass(frozen=True)
class Sources:
    """The logs a command on a criterion reads."""

    log: Path  # the one it appends to and judges into: the criterion's own, or the file --log or --out names
    experiments: list[Path]  # the criterion's experiments' logs, whose rows count as its own
    shared: list[Path]  # every other criterion's logs, whose baseline rows (base, diff, same) it borrows

    @property
    def own(self) -> list[Path]:
        """The logs whose rows are the criterion's, its own log last."""
        return [*self.experiments, self.log]


def sources(registry: Registry, criterion: str, given: str | None) -> Sources:
    """A file named by --log or --out (a smoke test, say) stands alone. Otherwise it's the criterion's own log
    and its experiments', with every other criterion's logs beside them: the baseline renders one prompt in
    every criterion, so each of its samples runs once and counts everywhere."""
    if given:
        return Sources(Path(given), [], [])
    return Sources(
        logs.log_path(criterion),
        logs.experiment_logs(criterion),
        [
            path
            for other in registry.criteria
            if other != criterion
            for path in [*logs.experiment_logs(other), logs.log_path(other)]
        ],
    )


def counted_rows(src: Sources) -> list[dict]:
    """The shared logs' baseline rows, then the criterion's own rows. Where two logs hold one (model, prompt
    hash, sample), the last row wins, so the criterion's own reply does, and its own log's over its
    experiments'."""
    borrowed = [
        row for path in src.shared for row in logs.load_rows(path) if row.get("condition") in BASELINE
    ]
    return borrowed + [row for path in src.own for row in logs.load_rows(path)]


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
    ns: list[int] | None = None,
) -> Replies:
    """The criterion's replies, only those of `conditions`, `models` and market sizes `ns` when given."""
    src = sources(registry, criterion, given)
    labels = {name: labels_beside(judge, [*src.shared, *src.own]) for name, judge in registry.judges.items()}
    rows = [
        row
        for row in counted_rows(src)
        if (conditions is None or row["condition"] in conditions)
        and (models is None or row["model"] in models)
        and (ns is None or row["n"] in ns)
    ]
    return prepare(registry, criterion, rows, labels)


def cmd_list(registry: Registry, args):
    """Each criterion and the question it asks, then its conditions, each with its slot levels, its question
    (ask) and its game. show, run --conditions and table --conditions take these names. Criteria named
    (or prefixed: conc) narrow it to theirs."""
    for name in args.criteria or registry.criteria:
        print(f"{name}: {registry.criteria[name].question}")
        for cond, spec in registry.conditions(name).items():
            parts = [f"{slot}={level}" for slot, level in spec.levels.items()]
            print(f"  {cond:<14} {' '.join([*parts, f'ask={spec.ask}', f'game={spec.game.name}'])}")


def cmd_show(registry: Registry, args):
    """One condition's prompt as a model gets it at n firms: the system prompt, then the user prompt. A prompt
    that names the model (the same_model framings, say) reads "the model" unless --model names one. It
    calls nothing."""
    try:
        name = NAMES[args.model] if args.model else MODEL
        p = registry.render(registry.condition(args.criterion, args.condition), args.n, name)
    except ValueError as e:
        sys.exit(str(e))
    print(f"[system] {p.system}\n\n{p.user}")


def cmd_run(registry: Registry, args):
    """Ask each model each condition, at each market size, --samples times, and append a row per call to the
    criterion's log, logs/<criterion>/results.jsonl.

    It skips every (model, prompt, sample) that already has a reply in the criterion's logs, its
    experiments' among them (logs/<criterion>/<id>/results.jsonl), or among the other criteria's baseline
    replies (base, diff, same render one prompt in every criterion). So raising --samples adds samples, a
    rerun retries the calls that failed, and a reworded condition starts afresh.

    Two runs may append to one log at once: each row goes in under a lock on the file.

    A file named with --out stands alone: run appends to it and skips only the replies it holds. Give a
    smoke test its own --out, so the criterion's log holds only runs you mean to keep. Claude and Codex models
    run on their subscriptions; OpenRouter models need OPENROUTER_API_KEY."""
    src = sources(registry, args.criterion, args.out)
    conditions = args.conditions or list(registry.conditions(args.criterion))
    try:
        tasks = plan(
            registry,
            args.criterion,
            conditions,
            args.models,
            args.ns,
            args.samples,
            done_keys(counted_rows(src)),
        )
    except ValueError as e:
        sys.exit(f"no calls made: {e}")
    if args.plan:
        every = sources(registry, args.criterion, None)  # prices come from every log, --out or not
        paths = dict.fromkeys([*every.shared, *every.own, src.log])
        print(plan_text(tasks, [row for path in paths for row in logs.load_rows(path)]))
        return
    run(tasks, src.log, workers=args.workers)


def plan_text(tasks: list[Task], rows: list[dict]) -> str:
    """The calls a run would make per model, their backend and their price, then the OpenRouter total."""
    found = estimate(tasks, rows)
    lines = [f"{len(tasks)} calls to make; --plan makes none"]
    for e in found:
        price = f"~${e.cost:.2f} (${e.cost / e.calls:.4f} a call), {e.basis}" if e.cost else e.basis
        lines.append(f"  {e.model:<9} {e.backend:<11} {e.calls:>5} calls  {price}")
    total = sum(e.cost for e in found if e.cost)
    unpriced = [e.model for e in found if e.cost is None]
    lines.append(f"OpenRouter: ~${total:.2f}" + (f", not counting {', '.join(unpriced)}" if unpriced else ""))
    return "\n".join(lines)


def cmd_judge(registry: Registry, args):
    """Label the replies the criterion's table counts, the borrowed baseline replies among them, with each
    judge (by default the copy judge: does the reply expect its rivals to match it, and act on that).

    Each label is one Claude call on the subscription. The labels go to the cache beside the criterion's own
    log, logs/<criterion>/judge-<name>.jsonl, keyed by a hash of the judge's model, its prompt and the reply,
    so a rerun labels only new replies. A reply already labelled in a cache beside another log, one of the
    criterion's experiments' or another criterion's, is left as it is. table and synth read the labels from
    all of these caches. With --log, only that file's replies and the cache beside it count."""
    src = sources(registry, args.criterion, args.log)
    texts = [row["reply"] for row in replies(registry, args.criterion, args.log).rows]
    for name in args.judges:
        judge = registry.judges[name]
        judged, failed, cached = label(
            judge,
            texts,
            logs.judge_path(src.log, name),
            known=labels_beside(judge, [*src.shared, *src.experiments]).keys(),
        )
        print(f"{name}: judged {judged}, {len(failed)} failed, {cached} already cached")
        for line in failed:
            print(f"  failed {line}")


def cmd_table(registry: Registry, args):
    """A markdown table of the criterion's replies, a line per condition, model and number of firms (n).

    replies, parsed      replies, and the ones with a number on their answer line
    median, IQR          of those numbers
    nash, cartel, naive  how many numbers sit at each focal point of the game (within 0.5)
    other focal          the same for the game's other focal points and the criterion's own
    other                numbers at none of them
    text answer          replies that answered on a text line instead, such as DECLINE
    judged, % copy       replies the copy judge labelled, and the share it finds state the copy premise
    % antitrust ...      the share whose text matches each word list in zerocommcartel/mentions.py

    Notes below the table count the replies to an older wording of their condition, which it leaves out, and
    the calls that failed with no reply yet. It reads what run and judge read (see their -h)."""
    found = filtered_replies(registry, args)
    if found is not None:
        print(table(registry, found), end="")


def filtered_replies(registry: Registry, args, empty_ok: bool = False) -> Replies | None:
    """The replies of the conditions, models and market sizes asked for. When none match: with `empty_ok`,
    the empty replies, else None, having said so. Exits on a condition the criterion lacks."""
    try:
        for name in args.conditions or []:
            registry.condition(args.criterion, name)
    except ValueError as e:
        sys.exit(str(e))
    found = replies(registry, args.criterion, args.log, args.conditions, args.models, args.ns)
    if (args.conditions or args.models or args.ns) and not found.rows and not empty_ok:
        print("No replies match the conditions, models and market sizes asked for.")
        return None
    return found


def cmd_grid(registry: Registry, args):
    """A grid per measure, for reading results across models: a line per condition and number of firms (n),
    a column per model and a last one pooling them ("all").

    Each cell counts the parsed answers (those with a number) as "k of m": with --at FOCAL, the ones at that
    focal point (within 0.5); with --below FOCAL, the ones more than 0.5 below it. A focal point is a name
    `zcc table` shows: nash, cartel, naive, or one of the condition's own, such as "copies vs nash". A cell
    whose condition has no such focal point shows "-". The grids come in the order the options are given;
    with neither, it's --at cartel. It reads what table reads."""
    found = filtered_replies(registry, args)
    if found is None:
        return
    measures = args.measures or [("cartel", False)]
    refuse_unknown_focal(found, measures)
    for focal, below in measures:
        print(f"## {'below' if below else 'at'} {focal}\n")
        print(grid(registry, found, focal, below))


def cmd_replies(registry: Registry, args):
    """The replies themselves, to read or quote: a count line, "k of N replies match", then a block per
    matching reply, tagged with its model, condition, number of firms (n), sample and parsed answer.

    N counts the replies left by --conditions, --models and --ns. A reply matches when it also passes every
    other filter given: --at and --below as in `zcc grid` (only replies with a parsed number pass them), and
    --grep, a Python regex searched in the reply's text (-i ignores case). Each block shows about 200
    characters around the first --grep match, or the reply's last 200 without --grep; --full shows whole
    replies, and --count only the count line. At most --limit blocks print (default 20); a last line says
    how many more matched. It reads what table reads."""
    found = filtered_replies(registry, args, empty_ok=True)
    assert found is not None  # empty_ok never gives None
    flags = re.MULTILINE | (re.IGNORECASE if args.ignore_case else 0)
    try:
        pattern = re.compile(args.grep, flags) if args.grep else None
    except re.error as e:
        sys.exit(f"bad --grep {args.grep!r}: {e}")
    measures = args.measures or []
    if found.rows:
        refuse_unknown_focal(found, measures)
    limit = 0 if args.count else args.limit
    print(
        quotes(matching(registry, found, measures, pattern), len(found.rows), pattern, args.full, limit),
        end="",
    )


def refuse_unknown_focal(found: Replies, measures: list[tuple[str, bool]]) -> None:
    """Exits naming any focal point in `measures` that none of the replies has."""
    named = {name for row in found.rows for name in row["focal"]}
    for focal in sorted({focal for focal, _ in measures} - named):
        sys.exit(f"no reply asked for has a focal point {focal!r}; theirs are {', '.join(sorted(named))}")


def cmd_synth(registry: Registry, args):
    """Is each criterion necessary for collusion? A table with a line per model and number of firms (n).

    same at cartel     of the parsed answers to `same` (each firm is told every firm asks this same AI model
                       with this same prompt), how many are at the cartel share, pooled over every
                       criterion's logs
    same deliberate    of the `same` replies the copy judge labelled, how many are at the cartel share and,
                       by the judge, expect the rivals to match whatever the firm picks (premise) and
                       maximize over the one quantity they then share (acts)
    <criterion>: ...   each criterion's measure, as hits/total

    If a criterion is necessary, every line with deliberate cartel answers passes its measure, and a line that
    colludes deliberately and fails it is a counterexample. Sufficiency isn't tested. A "-" means no replies,
    not a failure.

    A measure doesn't say which game it ran in. `same` is one-shot Cournot, but the capable criterion's
    measure (`joint`) runs in the repeated market, so a line can set the two games side by side, or show the
    measure with no `same` beside it. The compliant criterion has no measure yet."""
    print(synth(registry, [replies(registry, criterion, None) for criterion in registry.criteria]), end="")


def cmd_hashes(registry: Registry, args):
    """A line per prompt (criterion, condition, n, hash) and per judge (its key for an empty reply, which
    moves whenever its cached labels go stale). Diff it across a shared-core change to see which logs it
    ages: a changed prompt line means that cell's logged replies drop out of the tables as stale, and a
    changed judge line means that judge labels every reply anew."""
    for name in registry.criteria:
        for cond, spec in registry.conditions(name).items():
            for n in args.ns:
                with contextlib.suppress(ValueError):  # a market size the condition's game can't take
                    print(f"{name} {cond} {n} {registry.render(spec, n).hash}")
    for name, judge in registry.judges.items():
        print(f"judge {name} {judge.key('')}")


def filter_options(s: argparse.ArgumentParser, criteria: list[str], conditions: str, models: str) -> None:
    """The criterion, its --log, and the options that narrow its replies, which table, grid and replies share.
    `conditions` and `models` name, for the help, what each narrowing keeps (rows, columns, replies)."""
    criterion_argument(s, criteria)
    s.add_argument("--log", help=LOG_HELP)
    s.add_argument("--conditions", nargs="+", help=f"only these conditions' {conditions}; default: all")
    s.add_argument(
        "--models", nargs="+", choices=list(MODELS), help=f"only these models' {models}; default: all"
    )
    s.add_argument("--ns", nargs="+", type=int, help="only these numbers of firms; default: all")


def criterion_named(criteria: list[str], text: str) -> str:
    """The criterion named `text`, or else the one whose name starts with it."""
    if text in criteria:
        return text
    found = [name for name in criteria if name.startswith(text)]
    if len(found) == 1:
        return found[0]
    if found:
        raise argparse.ArgumentTypeError(f"{text!r} starts more than one criterion: {', '.join(found)}")
    raise argparse.ArgumentTypeError(f"no criterion is or starts with {text!r}")


def criterion_argument(
    s: argparse.ArgumentParser, criteria: list[str], dest: str = "criterion", **kwargs
) -> None:
    """A criterion, by its name or a prefix that no other criterion's name shares (conc for
    conceptualization)."""
    # type turns a prefix into the full name before choices checks it, so choices only lists the names in -h
    s.add_argument(dest, choices=criteria, type=lambda text: criterion_named(criteria, text), **kwargs)


def at_least_zero(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError(f"can't be negative: {value}")
    return value


def focal_options(s: argparse.ArgumentParser, help: str) -> None:
    """--at FOCAL and --below FOCAL, collected as (focal, below) pairs in args.measures."""
    for flag, below, what in (("--at", False, "at"), ("--below", True, "below")):
        s.add_argument(
            flag,
            dest="measures",
            action="extend",
            nargs="+",
            metavar="FOCAL",
            type=lambda focal, below=below: (focal, below),
            help=help.format(what=what),
        )


def main(argv=None, registry: Registry = REGISTRY):
    p = argparse.ArgumentParser(
        prog="zcc", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    def command(name: str, summary: str) -> argparse.ArgumentParser:
        """A subcommand whose -h shows its function's docstring. One without a docstring fails here, so no
        command's -h goes blank."""
        doc = COMMANDS[name].__doc__
        if not doc:
            raise ValueError(f"zcc {name}: its function has no docstring for -h to show")
        return sub.add_parser(
            name,
            help=summary,
            description=inspect.cleandoc(doc),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    criteria = list(registry.criteria)
    s = command("list", "each criterion and its conditions")
    criterion_argument(s, criteria, "criteria", nargs="*", help="only these criteria; default: all")
    s = command("show", "print one condition's prompt")
    criterion_argument(s, criteria)
    s.add_argument("condition", help="one of the criterion's conditions, as `zcc list` names them")
    s.add_argument("n", type=int, help="the number of firms in the market, such as 2, 3 or 4")
    s.add_argument("--model", choices=list(MODELS), help="the model a prompt names, if it names one")
    s = command("run", "ask the models, appending to the criterion's log")
    criterion_argument(s, criteria)
    s.add_argument("--conditions", nargs="+", help="default: all of the criterion's conditions")
    s.add_argument("--models", nargs="+", default=["haiku", "sonnet", "opus"])
    s.add_argument(
        "--ns", nargs="+", type=int, default=NS, help="numbers of firms; each game says which it takes"
    )
    s.add_argument("--samples", type=int, default=3)
    s.add_argument("--workers", type=int, default=40)
    s.add_argument("--out", help="default: logs/<criterion>/results.jsonl")
    s.add_argument(
        "--plan",
        action="store_true",
        help="print the calls per model and their OpenRouter price, and call nothing",
    )
    s = command("judge", "label the criterion's replies with judges (cached beside the log)")
    criterion_argument(s, criteria)
    s.add_argument("--judges", nargs="+", default=["copy"], choices=list(registry.judges))
    s.add_argument("--log", help=LOG_HELP)
    s = command("table", "a markdown table of the criterion's replies")
    filter_options(s, criteria, conditions="rows", models="rows")
    s = command("grid", "condition x model counts at a focal point, for results write-ups")
    filter_options(s, criteria, conditions="rows", models="columns")
    focal_options(s, "a grid of the answers {what} each focal point")
    s = command("replies", "the matching replies, counted and quoted with their tags")
    filter_options(s, criteria, conditions="replies", models="replies")
    focal_options(s, "only the answers {what} the focal point")
    s.add_argument("--grep", metavar="REGEX", help="only replies whose text matches this Python regex")
    s.add_argument("-i", "--ignore-case", action="store_true", help="--grep ignores case")
    shown = s.add_mutually_exclusive_group()
    shown.add_argument("--full", action="store_true", help="whole replies instead of snippets")
    shown.add_argument("--count", action="store_true", help="only the count line")
    s.add_argument("--limit", type=at_least_zero, default=20, help="at most this many replies (default 20)")
    command("synth", "is each criterion necessary? its measure beside same's cartel and deliberate rates")
    s = command("hashes", "prompt hashes and judge keys; diff them across a shared-core change")
    s.add_argument("--ns", nargs="+", type=int, default=NS, help="numbers of firms")
    args = p.parse_args(argv)
    COMMANDS[args.cmd](registry, args)


COMMANDS = {
    "list": cmd_list,
    "show": cmd_show,
    "run": cmd_run,
    "judge": cmd_judge,
    "table": cmd_table,
    "grid": cmd_grid,
    "replies": cmd_replies,
    "synth": cmd_synth,
    "hashes": cmd_hashes,
}
