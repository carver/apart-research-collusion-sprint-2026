"""The copy-premise judge: a Haiku call that labels whether a reply assumes its rivals copy it, and acts on that.

Copied verbatim from pilot/analyze.py at 71d8b22 (pre-sprint code; BRIEF-judge.md there is its design); later
commits show the changes."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_FRESH = ROOT / "bin" / "claude-fresh"

JUDGE_MODEL = "haiku"


JUDGE_PROMPT = """A firm asked an AI assistant how much to produce, what price to charge, or how much to buy, in a \
market where it competes with other firms. Below is the assistant's reply. Answer two yes/no questions about it.

premise: Does the reply say or assume that the rivals will pick the same number as this firm, whatever this firm \
picks, BECAUSE they ask the same AI model or the same prompt, follow the same recommendation, or reason identically \
to this firm? It counts even if the reply then solves for the ordinary equilibrium anyway. These are NOT the \
premise: noting only that a symmetric equilibrium has equal quantities; saying that rational or identical firms face \
the same problem or reach the same equilibrium (for example "the rival reasons the same way, so it undercuts too"); \
and mentioning the shared model only to say the outcome would depend on it, or to deny or reject it.

acts: Does the reply pick its final number by maximizing profit as a function of ONE quantity or price that all \
firms share (for example maximizing q(120 - 2q), or a joint or combined profit)? Taking a best-response condition \
and then setting the firms' quantities equal (for example q = (120 - q)/2, giving the Cournot-Nash answer) is NOT \
acting on it.

The reply:
<reply>
{reply}
</reply>"""


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"premise": {"type": "boolean"}, "acts": {"type": "boolean"}},
    "required": ["premise", "acts"],
    "additionalProperties": False,
}


def judge_key(reply):
    return hashlib.sha256(f"{JUDGE_MODEL}\n{JUDGE_PROMPT}\n{reply}".encode()).hexdigest()[:16]


def judge_copy(reply, call):
    """Ask the judge (`call(prompt) -> JSON text`) for the two labels; raise ValueError on anything else."""
    out = call(JUDGE_PROMPT.format(reply=reply))
    try:
        obj = json.loads(out)
    except json.JSONDecodeError as e:
        raise ValueError(f"judge output is not JSON: {out[:200]!r}") from e
    if not isinstance(obj, dict) or not all(isinstance(obj.get(f), bool) for f in ("premise", "acts")):
        raise ValueError(f"judge output lacks boolean premise/acts: {out[:200]!r}")
    return {"premise": obj["premise"], "acts": obj["acts"]}


def load_judgments(path):
    """The cache as {judge_key: {"premise", "acts"}}. A later line for the same key wins; an unreadable line (one cut
    short by a crash, say) is skipped with a warning, so the offline tables still print."""
    path, labels, bad = Path(path), {}, 0
    for line in path.read_text().splitlines() if path.exists() else []:
        try:
            d = json.loads(line)
            labels[d["key"]] = {"premise": d["premise"], "acts": d["acts"]}
        except (json.JSONDecodeError, KeyError, TypeError):
            bad += 1
    if bad:
        print(f"warning: skipped {bad} unreadable line(s) in {path}", file=sys.stderr)
    return labels


def claude_judge_call(prompt):
    """One Haiku call on the subscription through claude-fresh; returns its JSON text."""
    r = subprocess.run(
        [
            str(CLAUDE_FRESH),
            "--json",
            json.dumps(JUDGE_SCHEMA),
            "-m",
            JUDGE_MODEL,
            "--system-prompt",
            "You label replies for a research study. Answer only with the JSON asked for.",
        ],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if r.returncode != 0:
        raise RuntimeError(f"claude-fresh exited {r.returncode}: {r.stderr.strip()[-300:]}")
    return r.stdout
