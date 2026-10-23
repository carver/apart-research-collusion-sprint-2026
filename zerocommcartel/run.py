"""Running a lens's cells and logging each reply.

A cell is a condition at one market size, asked of one model; each sample of it is one call and one log row.
Each lens logs to its own file (zerocommcartel.logs.log_path).

A rerun skips the (model, prompt hash, sample) keys that already have a reply. So raising the sample count
adds samples, a failed call is retried, and rewording a condition starts its cells afresh."""

import concurrent.futures as cf
import json
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from zerocommcartel.answer import parse
from zerocommcartel.call import MODELS, complete
from zerocommcartel.lens import Registry
from zerocommcartel.logs import end_last_line
from zerocommcartel.prompt import Condition, Prompt


def done_keys(rows: Iterable[dict]) -> set[tuple[str, str, int]]:
    """The (model, prompt hash, sample) keys that have a reply."""
    return {(r["model"], r["prompt_hash"], r["sample"]) for r in rows if r.get("reply")}


@dataclass(frozen=True)
class Task:
    lens: str
    condition: str
    spec: Condition
    n: int
    model: str
    sample: int
    prompt: Prompt

    @property
    def key(self) -> tuple[str, str, int]:
        return (self.model, self.prompt.hash, self.sample)


def plan(
    registry: Registry,
    lens: str,
    conditions: Sequence[str],
    models: Sequence[str],
    ns: Sequence[int],
    samples: int,
    done: set[tuple[str, str, int]] | frozenset = frozenset(),
) -> list[Task]:
    """The calls a run makes, sample by sample, leaving out the `done` keys. Every prompt is rendered first,
    so a cell that can't run raises ValueError before any call."""
    specs = registry.conditions(lens)
    for name in conditions:
        if name not in specs:
            raise ValueError(f"lens {lens!r} has no condition {name!r}; it has {', '.join(specs)}")
    for model in models:
        if model not in MODELS:
            raise ValueError(f"unknown model {model!r}; models: {', '.join(MODELS)}")
    prompts = {(name, n): registry.render(specs[name], n) for name in conditions for n in ns}
    tasks = [
        Task(lens, name, specs[name], n, model, sample, prompt)
        for sample in range(samples)
        for model in models
        for (name, n), prompt in prompts.items()
    ]
    return [t for t in tasks if t.key not in done]


def one(task: Task, call: Callable) -> dict:
    """Ask the model once and return the log row. A failed call is a row with its error, which a rerun
    retries."""
    p, spec = task.prompt, task.spec
    row = {
        "model": task.model,
        "model_id": MODELS[task.model][1],
        "lens": task.lens,
        "condition": task.condition,
        "levels": spec.levels,
        "ask": spec.ask,
        "game": spec.game.name,
        "game_params": spec.game.params(),
        "n": task.n,
        "sample": task.sample,
        "prompt_hash": p.hash,
        "t": time.time(),
    }
    t0 = time.monotonic()
    try:
        reply, meta = call(task.model, p.system, p.user)
        a = parse(reply, p.number_key, p.text_keys)
        row.update(reply=reply, answer=a.key, value=a.value, text=a.text, error=None, **meta)
    except Exception as e:  # keep going; the row records the failure and a rerun retries it
        row.update(reply=None, answer=None, value=None, text=None, error=str(e)[:500])
    row["seconds"] = round(time.monotonic() - t0, 1)
    return row


def run(
    tasks: Sequence[Task], out: Path, call: Callable = complete, workers: int = 40, say: Callable = print
) -> tuple[int, int]:
    """Make the calls in parallel, appending each row to `out` as it comes back. Returns (ok, failed)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    end_last_line(out)
    ok = failed = 0
    say(f"{len(tasks)} calls to make")
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        for i, fut in enumerate(cf.as_completed([pool.submit(one, t, call) for t in tasks]), 1):
            row = fut.result()
            with out.open("a") as f:
                f.write(json.dumps(row) + "\n")
            ok, failed = ok + (row["error"] is None), failed + (row["error"] is not None)
            if i % 20 == 0 or row["error"]:
                error = f" ERR {row['error'][:120]}" if row["error"] else ""
                say(
                    f"[{i}/{len(tasks)}] ok {ok} fail {failed}  last: {row['model']} {row['condition']} "
                    f"n={row['n']} -> {row['answer']} {row['value']}{error}"
                )
    say(f"done: ok {ok}, failed {failed}")
    return ok, failed
