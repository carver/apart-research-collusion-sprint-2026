"""Run logs: every message a run processes, one JSON object per line, written as it goes.

A run's log is ``logs/<experiment>/<start time, UTC>.jsonl`` in the project root. The first line
describes the run (experiment, start time, settings). Every other line is one message, with its type
name, in the order the queue processed it.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .messages import Message

LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"


class RunLog:
    def __init__(self, experiment: str, **settings: Any) -> None:
        started = datetime.now(UTC)
        self.path = LOGS_DIR / experiment / f"{started:%Y-%m-%dT%H-%M-%SZ}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        header = {
            "type": "RunStarted",
            "experiment": experiment,
            "started": started.isoformat(timespec="seconds"),
        }
        with self.path.open("x") as file:  # "x": never overwrite an existing log
            file.write(json.dumps({**header, **settings}, ensure_ascii=False) + "\n")

    def write(self, message: Message) -> None:
        record = {"type": type(message).__name__, **message.model_dump(mode="json")}
        with self.path.open("a") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
