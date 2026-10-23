"""Where the pilot's scripts read and write, and which claude-fresh they run: the repo's own copy in bin/,
so a collaborator without llm-toolbox on PATH can run them. No test calls a model."""

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(f"pilot_{name}", ROOT / "pilot" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recording_run(stdout):
    """A stand-in for subprocess.run that records each argv and answers with `stdout`."""
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    run.calls = calls
    return run


def test_the_probe_asks_claude_through_the_repos_claude_fresh(monkeypatch):
    probe = load("probe")
    run = recording_run("QUANTITY: 30")
    monkeypatch.setattr(subprocess, "run", run)

    assert probe.call_claude("haiku", "system", "prompt") == "QUANTITY: 30"
    assert run.calls[0][0] == str(ROOT / "bin" / "claude-fresh")


def test_the_judge_asks_claude_through_the_repos_claude_fresh(monkeypatch):
    analyze = load("analyze")
    run = recording_run('{"premise": true, "acts": true}')
    monkeypatch.setattr(subprocess, "run", run)

    analyze.claude_judge_call("prompt")
    assert run.calls[0][0] == str(ROOT / "bin" / "claude-fresh")


def test_a_probe_run_creates_its_results_folder(tmp_path, monkeypatch):
    probe = load("probe")
    monkeypatch.setattr(subprocess, "run", recording_run("Each firm should make 30.\nQUANTITY: 30"))
    out = tmp_path / "logs" / "pilot" / "probe-results.jsonl"

    probe.main(
        ["run", "--models", "haiku", "--arms", "same", "--ns", "2", "--samples", "1", "--out", str(out)]
    )

    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert [(r["model"], r["arm"], r["n"], r["value"]) for r in rows] == [("haiku", "same", 2, 30.0)]


def test_the_judge_creates_its_cache_folder(tmp_path):
    analyze = load("analyze")
    results = tmp_path / "results.jsonl"
    reply = {"model": "haiku", "game": "cournot", "arm": "same", "n": 2, "sample": 0, "value": 30.0}
    results.write_text(json.dumps({**reply, "reply": "We all follow one answer. QUANTITY: 30"}) + "\n")
    cache = tmp_path / "logs" / "pilot" / "judge-copy.jsonl"

    analyze.main(
        ["judge", "--file", str(results), "--cache", str(cache), "--gold", str(tmp_path / "gold.jsonl")],
        call=lambda prompt: '{"premise": true, "acts": true}',
    )

    labels = [json.loads(line) for line in cache.read_text().splitlines()]
    assert [(label["premise"], label["acts"]) for label in labels] == [(True, True)]


def test_results_and_judge_labels_default_to_logs_pilot_and_the_gold_set_to_pilot():
    probe, analyze = load("probe"), load("analyze")

    assert probe.RESULTS == ROOT / "logs" / "pilot" / "probe-results.jsonl"
    assert analyze.RESULTS == ROOT / "logs" / "pilot" / "probe-results.jsonl"
    assert analyze.JUDGE_CACHE == ROOT / "logs" / "pilot" / "judge-copy.jsonl"
    assert analyze.JUDGE_GOLD == ROOT / "pilot" / "judge-gold.jsonl"
