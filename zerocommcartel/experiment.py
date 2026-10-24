"""An experiment from EXPERIMENT_IDEAS.md as one rerunnable script: its cells, its judges and its report.

Each script in experiments/ declares an `Experiment` and calls `main`, which prints how many calls the
experiment makes, makes the ones its log lacks, has its judges label the replies, and prints its report:

    uv run python experiments/cap1_joint_optimum.py             # run what's missing, judge, report
    uv run python experiments/cap1_joint_optimum.py --dry-run   # count the calls, make none
    uv run python experiments/cap1_joint_optimum.py --fresh     # every call again, in a new dated log

Each experiment has a folder of its own inside its criterion's, named by its id: CAP-2's replies go to
logs/capable/cap2/results.jsonl, its judges' labels beside them, and a --fresh run to
logs/capable/cap2/results-<date>-<time>.jsonl. An experiment whose report compares its cells with another's
(CAP-3 with the baselines) reads that experiment's log as it is and makes none of its calls.

OpenRouter models need OPENROUTER_API_KEY; when it isn't set, the repo's .env is read for it."""

import argparse
import os
import time
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass
from pathlib import Path

from zerocommcartel import logs
from zerocommcartel.call import complete, route
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criterion import Registry
from zerocommcartel.judge import claude_call, label, load_labels
from zerocommcartel.run import done_keys, plan, run
from zerocommcartel.table import Replies, prepare

DOTENV = Path(__file__).resolve().parent.parent / ".env"


@dataclass(frozen=True)
class Experiment:
    id: str  # its id in EXPERIMENT_IDEAS.md, such as "CAP-1"
    name: str
    criterion: str
    conditions: tuple[str, ...]
    models: tuple[str, ...]
    ns: tuple[int, ...]  # market sizes
    samples: int  # calls per cell: a condition at one market size, asked of one model
    judges: tuple[str, ...]
    report: Callable[[Replies], str]  # the experiment's tables, from its replies
    compare: tuple[str, ...] = ()  # folders in logs/ ("capable/baselines") whose replies the report shows too

    @property
    def calls(self) -> int:
        return len(self.models) * len(self.conditions) * len(self.ns) * self.samples

    @property
    def folder(self) -> str:
        """The experiment's folder in logs/: its criterion's, then its id, lowercased, without the dash
        ("capable/cap2")."""
        return f"{self.criterion}/{self.id.lower().replace('-', '')}"

    def log(self) -> Path:
        return logs.LOGS / self.folder / "results.jsonl"

    def fresh_log(self) -> Path:
        """A new log in the experiment's folder, named by the minute it starts."""
        return self.log().with_name(f"results-{time.strftime('%Y-%m-%d-%H%M')}.jsonl")

    def mine(self, row: dict) -> bool:
        return row["condition"] in self.conditions and row["model"] in self.models and row["n"] in self.ns


def plural(k: int, word: str) -> str:
    return f"{k} {word}{'' if k == 1 else 's'}"


def load_env(path: Path, environ: MutableMapping[str, str]):
    """Sets OPENROUTER_API_KEY from the KEY=VALUE lines of `path` when `environ` lacks it."""
    if "OPENROUTER_API_KEY" in environ or not path.exists():
        return
    for line in path.read_text().splitlines():
        key, _, value = line.strip().partition("=")
        if key == "OPENROUTER_API_KEY" and value:
            environ[key] = value.strip().strip("\"'")


def main(
    experiment: Experiment,
    argv=None,
    registry: Registry = REGISTRY,
    call: Callable = complete,
    judge_call: Callable = claude_call,
):
    p = argparse.ArgumentParser(description=f"{experiment.id} {experiment.name}")
    p.add_argument("--dry-run", action="store_true", help="count the calls, make none")
    p.add_argument("--fresh", action="store_true", help="make every call again, in a new dated log")
    p.add_argument("--log", help="default: the experiment's own, logs/<criterion>/<id>/results.jsonl")
    args = p.parse_args(argv)
    e = experiment
    log = e.fresh_log() if args.fresh else Path(args.log) if args.log else e.log()
    done = done_keys(logs.load_rows(log))
    tasks = plan(registry, e.criterion, e.conditions, e.models, e.ns, e.samples, done)
    print(
        f"{e.id} {e.name}: {plural(len(e.models), 'model')} x {plural(len(e.conditions), 'condition')} x "
        f"{plural(len(e.ns), 'market size')} x {plural(e.samples, 'sample')} = {e.calls} calls; "
        f"{len(tasks)} to make, into {log}"
    )
    routes = {m: route(m) for m in e.models}
    print("routes: " + ", ".join(f"{m} {model_id} ({backend})" for m, (backend, model_id) in routes.items()))
    if args.dry_run:
        return
    if any(backend == "openrouter" for backend, _ in routes.values()):
        load_env(DOTENV, os.environ)
    if tasks:
        run(tasks, log, call)
    rows = [r for r in logs.load_rows(log) if e.mine(r)]
    for name in e.judges:
        judge = registry.judges[name]
        judged, failed, cached = label(
            judge, [r["reply"] for r in rows if r.get("reply")], logs.judge_path(log, name), judge_call
        )
        print(f"{name}: judged {judged}, {len(failed)} failed, {cached} already labelled")
    beside = [
        r
        for folder in e.compare
        for r in logs.load_rows(logs.LOGS / folder / "results.jsonl")
        if r["model"] in e.models and r["n"] in e.ns
    ]
    # a judge's labels for the compared rows sit beside their own log, written by their own script
    logged = [log, *(logs.LOGS / folder / "results.jsonl" for folder in e.compare)]
    labels = {
        name: {
            key: found
            for path in logged
            for key, found in load_labels(registry.judges[name], logs.judge_path(path, name)).items()
        }
        for name in e.judges
    }
    print(e.report(prepare(registry, e.criterion, rows + beside, labels)))
