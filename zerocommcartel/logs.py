"""Where the logs live, and reading and appending JSONL that a killed run may have cut short.

A criterion's log, logs/<criterion>/results.jsonl, has one row per call (zerocommcartel.run.ask_once
writes it):

    model, model_id       the MODELS key and the id it calls
    criterion, condition  the criterion and the condition's name
    levels, ask           the condition's slot levels and question (own, plain, best, joint or forecast)
    game, game_params     the game's name and parameters
    n, sample             the market size and the sample's number
    prompt_hash           the system and user prompt's hash; resume keys on (model, prompt_hash, sample)
    t, seconds            the call's start (Unix time) and length
    reply, error          the reply, or the error of a failed call (reply None)
    answer                the key of the reply's last answer line (QUANTITY, RIVAL, DECLINE...), or None
    value, text           that line's number, or its text on a text line
    provider, served_model, prompt_tokens, completion_tokens, cost    OpenRouter models only
    prompt_tokens, completion_tokens, reasoning_tokens, tool_calls, reasoning_effort    Codex models only

An experiment's script (zerocommcartel/experiment.py) writes the same rows to a folder of its own instead,
logs/<criterion>/<id>/results.jsonl (logs/capable/cap2/). zcc counts them as the criterion's
(`experiment_logs`).

The readers began as copies of pilot/probe.py's (71d8b22)."""

import json
import sys
from pathlib import Path

LOGS = Path(__file__).resolve().parent.parent / "logs"


def log_path(criterion: str) -> Path:
    """A criterion's own log, which `zcc run` appends to. Each criterion has its own folder, so two people
    running different criteria never write one file."""
    return LOGS / criterion / "results.jsonl"


def experiment_logs(criterion: str) -> list[Path]:
    """The logs of a criterion's experiments, one in each folder inside its own, by folder name. A folder that
    holds only judges' caches (an experiment that labels another's replies, such as CPL-1) still gets its
    path, so the caches beside it are read. A --fresh run's dated log is left out: it asks the same samples
    again under the same keys, and a table counts one reply per key."""
    folder = LOGS / criterion
    if not folder.is_dir():
        return []
    return sorted(path / "results.jsonl" for path in folder.iterdir() if path.is_dir())


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
