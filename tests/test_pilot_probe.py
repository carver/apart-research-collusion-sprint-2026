"""Tests of pilot/probe.py's `run` command: which calls it makes on a resume, and when it refuses to make any.
No test calls a model: subprocess.run is faked, so claude-fresh never runs.

pilot/ is a folder of scripts, not a package, so probe.py is loaded by file path."""

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

_spec = importlib.util.spec_from_file_location(
    "pilot_probe", Path(__file__).resolve().parent.parent / "pilot" / "probe.py"
)
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


@pytest.fixture
def prompts(monkeypatch):
    """The prompts each claude-fresh call is sent; every call answers QUANTITY: 30."""
    sent = []

    def run(argv, input=None, **kwargs):
        sent.append(input)
        return SimpleNamespace(returncode=0, stdout="QUANTITY: 30", stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    return sent


def run_probe(out, *args):
    probe.main(["run", "--models", "haiku", "--samples", "1", "--out", str(out), *args])


@pytest.mark.parametrize(
    "args, bad",
    [
        (["--game", "kyleq"], ["mono", "base", "diff", "hub", "hubjoint", "samerep"]),  # the default arms
        (["--game", "kylel", "--arms", "base", "same", "--ns", "2"], ["base"]),
        (["--game", "cournot", "--arms", "same", "report", "--ns", "2"], ["report"]),
    ],
)
def test_a_run_with_arms_its_game_does_not_take_is_refused_before_any_call(tmp_path, prompts, args, bad):
    out = tmp_path / "results.jsonl"

    with pytest.raises(SystemExit) as refused:
        run_probe(out, *args)

    message = str(refused.value.code)
    assert all(arm in message for arm in bad), message
    assert prompts == []
    assert not out.exists()


def row(sample, reply):
    return {"model": "haiku", "game": "cournot", "arm": "same", "n": 2, "sample": sample, "reply": reply}


CUT_SHORT = '{"model": "haiku", "game": "cournot", "arm": "same", "n": 2, "sam'


@pytest.mark.parametrize("broken", [CUT_SHORT, "42"])
def test_a_run_resumes_past_an_unreadable_last_line(tmp_path, prompts, capsys, broken):
    out = tmp_path / "results.jsonl"
    done = json.dumps(row(0, "QUANTITY: 30"))
    out.write_text(done + "\n" + broken)

    run_probe(out, "--game", "cournot", "--arms", "same", "--ns", "2", "--samples", "2")

    assert len(prompts) == 1
    assert "skipped 1 unreadable line" in capsys.readouterr().err
    lines = out.read_text().splitlines()
    assert lines[:2] == [done, broken]  # the new reply starts a line of its own, not glued to the broken one
    assert [json.loads(line)["sample"] for line in lines[2:]] == [1]
