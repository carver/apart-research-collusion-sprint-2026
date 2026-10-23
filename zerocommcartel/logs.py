"""Where the logs live, and reading and appending JSONL that a killed run may have cut short.

The readers began as copies of pilot/probe.py's (71d8b22)."""

import json
import sys
from pathlib import Path

LOGS = Path(__file__).resolve().parent.parent / "logs"


def log_path(lens: str) -> Path:
    """A lens's replies. Each lens has its own folder, so two people running different lenses never write one
    file."""
    return LOGS / lens / "results.jsonl"


def judge_path(log: Path, judge: str) -> Path:
    """A judge's cache, beside the log whose replies it judges. Its keys hash the reply, so logs that share a
    folder can share it."""
    return log.parent / f"judge-{judge}.jsonl"


def load_rows(path: Path) -> list[dict]:
    """The file's rows, in order. An unreadable line (one cut short by a killed run, say) is skipped with a
    warning."""
    rows, bad = [], 0
    for line in path.read_text().splitlines() if path.exists() else []:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            bad += 1
    if bad:
        print(f"warning: skipped {bad} unreadable line(s) in {path}", file=sys.stderr)
    return rows


def end_last_line(path: Path):
    """Ends a file whose last line was cut short (a run killed mid-write), so the next row starts a line of
    its own."""
    if path.exists() and path.read_bytes()[-1:] not in (b"", b"\n"):
        with path.open("a") as f:
            f.write("\n")
