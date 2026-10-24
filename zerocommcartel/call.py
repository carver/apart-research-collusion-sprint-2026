"""Model callers: Claude through bin/claude-fresh (the Claude subscription), OpenAI's models through the Codex
CLI (the ChatGPT subscription), the rest through OpenRouter over HTTP.

Copied verbatim from pilot/probe.py at 71d8b22 (pre-sprint code); later commits show the changes."""

import json
import os
import random
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_FRESH = ROOT / "bin" / "claude-fresh"

MODELS = {  # key: (backend, id)
    "haiku": ("claude", "haiku"),
    "sonnet": ("claude", "sonnet"),
    "opus": ("claude", "opus"),
    "nemotron": ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"),
    "minimax": ("openrouter", "minimax/minimax-m3.1-flash:free"),
    "gemma": ("openrouter", "google/gemma-4-31b-it:free"),
    "inkling": ("openrouter", "thinkingmachines/inkling:free"),
    "dots": ("openrouter", "dots-studio/dots-3-note-preview:free"),
    "laguna": ("openrouter", "poolside/laguna-s-2.1:free"),
    "luna": ("codex", "gpt-6-luna"),
    "astra": ("codex", "gpt-6-astra"),
    "glm": ("openrouter", "z-ai/glm-5.3"),
}


class CallFailed(Exception):
    pass


_claude_slots = threading.Semaphore(12)


def call_claude(model_id: str, system: str, prompt: str) -> str:
    last = ""
    for attempt in range(3):
        with _claude_slots:
            r = subprocess.run(
                [str(CLAUDE_FRESH), "--text", "-m", model_id, "--system-prompt", system, "-t", "600"],
                input=prompt,
                capture_output=True,
                text=True,
            )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
        last = (r.stderr or r.stdout)[-400:]
        time.sleep(5 * (attempt + 1))
    raise CallFailed(f"claude {model_id}: {last}")


class RateLimiter:
    """Spaces request starts at least 60/rpm seconds apart, across threads."""

    def __init__(self, rpm: float):
        self.interval, self._next, self._lock = 60.0 / rpm, 0.0, threading.Lock()

    def wait(self):
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + self.interval
        time.sleep(max(0.0, start - now))


_limiters: dict[str, RateLimiter] = {}


_or_slots: dict[str, threading.Semaphore] = {}


_or_lock = threading.Lock()


RPM = 18


PAID_OK = {
    "z-ai/glm-5.3",  # approved 2026-10-23, for the communal criterion (#41)
}


def call_openrouter(model_id: str, system: str, prompt: str) -> tuple[str, dict]:
    if not model_id.endswith(":free") and model_id not in PAID_OK:
        raise CallFailed(f"{model_id} is neither free nor in PAID_OK")
    with _or_lock:
        limiter = _limiters.setdefault(model_id, RateLimiter(RPM))
        slots = _or_slots.setdefault(model_id, threading.Semaphore(8))
    body = json.dumps(
        {
            "model": model_id,
            "max_tokens": 8000,
            "usage": {"include": True},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        }
    ).encode()
    last = ""
    for attempt in range(7):
        limiter.wait()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json",
            },
        )
        try:
            with slots, urllib.request.urlopen(req, timeout=300) as resp:
                data = json.load(resp)
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
            if content and content.strip():
                u = data.get("usage") or {}
                return content, {
                    "provider": data.get("provider"),
                    "served_model": data.get("model"),
                    "prompt_tokens": u.get("prompt_tokens"),
                    "completion_tokens": u.get("completion_tokens"),
                    "cost": u.get("cost"),
                }
            last = f"empty content: {json.dumps(data)[:300]}"
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:300]!r}"
            if e.code not in (408, 429) and e.code < 500:
                raise CallFailed(f"{model_id}: {last}") from e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as e:
            last = repr(e)
        time.sleep(min(90, 6 * 2**attempt) * random.uniform(0.7, 1.3))
    raise CallFailed(f"{model_id}: {last}")


# Codex's own default for gpt-6-astra and gpt-6-luna, pinned so ~/.codex/config.toml can't change it
CODEX_EFFORT = "medium"
# Codex features that give the model tools. Off, so a reply is one model turn, as with claude-fresh. No flag
# removes the last few built-in tools (a clock, agent messages); a reply that uses one counts in tool_calls.
CODEX_OFF = (
    "shell_tool",
    "unified_exec",
    "code_mode_host",
    "apps",
    "plugins",
    "multi_agent",
    "image_generation",
    "browser_use",
    "computer_use",
    "in_app_browser",
    "view_image",
    "hooks",
    "goals",
    "skill_search",
    "tool_suggest",
    "sleep_tool",
)
NOT_TOOLS = {"agent_message", "reasoning", "error"}  # completed items that aren't a tool call
_codex_slots = threading.Semaphore(4)


def codex_command(model_id: str, instructions: Path) -> list[str]:
    """`codex exec` locked down like bin/claude-fresh: no user config, rules, saved session or tools, the
    model and effort pinned, and the file `instructions` (the system prompt) in place of Codex's own. Prompt
    on stdin, events on stdout as JSON lines."""
    cmd = ["codex", "exec", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check", "--ephemeral"]
    cmd += ["-s", "read-only", "-m", model_id, "-c", f"model_reasoning_effort={CODEX_EFFORT}"]
    cmd += ["-c", f"model_instructions_file={json.dumps(str(instructions))}", "-c", 'web_search="disabled"']
    for feature in CODEX_OFF:
        cmd += ["--disable", feature]
    return [*cmd, "--json", "-"]


def _events(stdout: str) -> list[dict]:
    """The JSON objects among codex's output lines."""
    events = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _fields(events: list[dict], kind: str, field: str) -> list[dict]:
    """The `field` object of each event of type `kind`."""
    return [e[field] for e in events if e.get("type") == kind and isinstance(e.get(field), dict)]


def _failure(events: list[dict]) -> str:
    """Why codex gave no reply: its failed turn's error, else its last error event's message."""
    failed = [e.get("error") for e in events if e.get("type") == "turn.failed"]
    errors = [e for e in events if e.get("type") == "error"]
    for error in reversed(errors + failed):
        message = error.get("message") if isinstance(error, dict) else error
        if message:
            return str(message)
    return "no agent message"


def codex_reply(stdout: str) -> tuple[str, dict]:
    """The last agent message in `codex exec --json` output, with the turn's token counts and how many tool
    calls the model made. Raises CallFailed, with codex's reason, when there's no message."""
    events = _events(stdout)
    items = _fields(events, "item.completed", "item")
    texts = [str(i.get("text") or "") for i in items if i.get("type") == "agent_message"]
    texts = [t for t in texts if t.strip()]
    if not texts:
        raise CallFailed(_failure(events))
    turns = _fields(events, "turn.completed", "usage")
    usage = turns[-1] if turns else {}
    return texts[-1], {
        "prompt_tokens": usage.get("input_tokens"),
        "completion_tokens": usage.get("output_tokens"),
        "reasoning_tokens": usage.get("reasoning_output_tokens"),
        "tool_calls": sum(i.get("type") not in NOT_TOOLS for i in items),
    }


def _codex_once(model_id: str, system: str, prompt: str) -> tuple[str, dict]:
    """One `codex exec`, run from an empty directory (so no AGENTS.md loads) and without OPENAI_API_KEY (so it
    bills the ChatGPT login, never an API key)."""
    env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
    with tempfile.TemporaryDirectory(prefix="codex-fresh-") as tmp:
        instructions, empty = Path(tmp) / "instructions.md", Path(tmp) / "work"
        instructions.write_text(system)
        empty.mkdir()
        try:
            r = subprocess.run(
                codex_command(model_id, instructions),
                input=prompt,
                capture_output=True,
                text=True,
                cwd=empty,
                env=env,
                timeout=600,
            )
        except subprocess.TimeoutExpired as e:
            raise CallFailed("timed out after 600s") from e
    if r.returncode != 0:
        raise CallFailed(f"exited {r.returncode}: {r.stderr.strip()[-400:] or _failure(_events(r.stdout))}")
    return codex_reply(r.stdout)


def call_codex(model_id: str, system: str, prompt: str) -> tuple[str, dict]:
    last = ""
    for attempt in range(3):
        try:
            with _codex_slots:
                reply, meta = _codex_once(model_id, system, prompt)
            return reply, {**meta, "reasoning_effort": CODEX_EFFORT}
        except CallFailed as e:
            last = str(e)
        time.sleep(5 * (attempt + 1))
    raise CallFailed(f"codex {model_id}: {last}")


def complete(model: str, system: str, user: str) -> tuple[str, dict]:
    """One reply from `model` (a key of MODELS), with the OpenRouter usage and provider when it has them."""
    backend, model_id = MODELS[model]
    if backend == "claude":
        return call_claude(model_id, system, user), {}
    if backend == "codex":
        return call_codex(model_id, system, user)
    return call_openrouter(model_id, system, user)
