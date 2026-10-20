"""Run logs: every message a run processes, one JSON object per line, written as it goes.

A run's log is ``logs/<experiment>/<start time, UTC>.jsonl`` in the project root. The first line
describes the run (experiment, start time, git commit, settings). After it, in the order they
happened, come the messages, with their type names, in the order the queue processed them, and after
each LLM agent's turn a ``TurnUsage`` line: the tokens and dollar cost of that turn's model requests.
``finish`` writes the last line, ``RunFinished``, with the usage totals for the run, per model and
per agent.
"""

import json
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .agent import TurnUsage
from .messages import Message

ROOT = Path(__file__).resolve().parents[2]  # the project root
LOGS_DIR = ROOT / "logs"


@dataclass
class UsageTotal:
    """The usage of several turns added up. ``cost`` counts only the turns that reported one; the
    others are counted in ``turns_without_cost``."""

    turns: int = 0
    turns_without_cost: int = 0
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost: float = 0.0

    def add(self, usage: TurnUsage) -> None:
        self.turns += 1
        self.requests += usage.requests
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.reasoning_tokens += usage.reasoning_tokens
        if usage.cost is None:
            self.turns_without_cost += 1
        else:
            self.cost += usage.cost

    def describe(self) -> str:
        text = (
            f"{self.turns} turns, {self.requests} requests, {self.input_tokens:,} in / "
            f"{self.output_tokens:,} out ({self.reasoning_tokens:,} reasoning) tokens, ${self.cost:.4f}"
        )
        if self.turns_without_cost:
            text += f" ({self.turns_without_cost} turns reported no cost)"
        return text


class RunLog:
    """``folder`` is where logs go, one subfolder per experiment; by default the project's
    ``logs/``."""

    def __init__(self, experiment: str, folder: Path | None = None, **settings: Any) -> None:
        started = datetime.now(UTC)
        self.path = (folder or LOGS_DIR) / experiment / f"{started:%Y-%m-%dT%H-%M-%SZ}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        header = {
            "type": "RunStarted",
            "experiment": experiment,
            "started": started.isoformat(timespec="seconds"),
            **git_state(),
        }
        with self.path.open("x") as file:  # "x": never overwrite an existing log
            file.write(json.dumps({**header, **settings}, ensure_ascii=False) + "\n")
        self.total = UsageTotal()
        self.by_model: defaultdict[str, UsageTotal] = defaultdict(UsageTotal)
        self.by_agent: defaultdict[str, UsageTotal] = defaultdict(UsageTotal)

    def write(self, message: Message) -> None:
        self._append({"type": type(message).__name__, **message.model_dump(mode="json")})

    def write_usage(self, agent: str, time: float, usage: TurnUsage) -> None:
        self._append({"type": "TurnUsage", "agent": agent, "time": time, **asdict(usage)})
        for total in (self.total, self.by_model[usage.model], self.by_agent[agent]):
            total.add(usage)

    def finish(self) -> dict[str, Any]:
        """Write the last line, the usage totals for the whole run, per model and per agent, and
        return them."""
        totals = {
            "total": asdict(self.total),
            "by_model": {model: asdict(total) for model, total in self.by_model.items()},
            "by_agent": {agent: asdict(total) for agent, total in self.by_agent.items()},
        }
        self._append({"type": "RunFinished", **totals})
        return totals

    def describe_totals(self) -> str:
        """The usage totals per model and for the whole run, one line each, for printing."""
        rows = [*self.by_model.items(), ("total", self.total)]
        return "\n".join(f"{name}: {total.describe()}" for name, total in rows)

    def _append(self, record: dict[str, Any]) -> None:
        with self.path.open("a") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def git_state() -> dict[str, Any]:
    """Which code a run used: the current git commit, and whether any files other than logs had
    uncommitted changes. Both are None if git can't tell."""

    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout

    try:
        commit = git("rev-parse", "HEAD").strip()
        changes = git("status", "--porcelain", "--", ".", ":(exclude)logs")
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "uncommitted_changes": None}
    return {"commit": commit, "uncommitted_changes": bool(changes)}
