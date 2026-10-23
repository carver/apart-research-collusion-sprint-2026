"""The runner's log handling.

Copied verbatim from pilot/probe.py at 71d8b22 (pre-sprint code); later commits show the changes."""

import json
import sys
from pathlib import Path


def done_keys(path: Path) -> set:
    """The keys that have a reply. An unreadable line (one cut short by a killed run, say) is skipped with a warning."""
    keys, bad = set(), 0
    for line in path.read_text().splitlines() if path.exists() else []:
        try:
            r = json.loads(line)
            if r.get("reply"):
                keys.add((r["model"], r["game"], r["arm"], r["n"], r["sample"]))
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            bad += 1
    if bad:
        print(f"warning: skipped {bad} unreadable line(s) in {path}", file=sys.stderr)
    return keys


def end_last_line(path: Path):
    """Ends a file whose last line was cut short (a run killed mid-write), so the next row starts a line of its own."""
    if path.exists() and path.read_bytes()[-1:] not in (b"", b"\n"):
        with path.open("a") as f:
            f.write("\n")
