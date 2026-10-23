"""Model callers: Claude through bin/claude-fresh (the subscription), OpenRouter over HTTP.

Copied verbatim from pilot/probe.py at 71d8b22 (pre-sprint code); later commits show the changes."""

import json
import os
import random
import subprocess
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
    "luna": ("openrouter", "openai/gpt-6-luna"),
    "astra": ("openrouter", "openai/gpt-6-astra"),
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


PAID_OK = {"openai/gpt-6-luna", "openai/gpt-6-astra"}  # paid panels Jason approved, 2026-10-20


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


def complete(model: str, system: str, user: str) -> tuple[str, dict]:
    """One reply from `model` (a key of MODELS), with the OpenRouter usage and provider when it has them."""
    backend, model_id = MODELS[model]
    if backend == "claude":
        return call_claude(model_id, system, user), {}
    return call_openrouter(model_id, system, user)
