"""The zcc command line. claude-fresh is faked (subprocess.run), so no test calls a model."""

import json
import subprocess
from types import SimpleNamespace

import pytest

from zerocommcartel.cli import main
from zerocommcartel.lenses import REGISTRY
from zerocommcartel.prompt import Condition


@pytest.fixture
def claude(monkeypatch):
    """The prompts each claude-fresh call gets. Replies say QUANTITY: 30; a judge says yes to both labels."""
    sent = []

    def run(argv, input=None, **kwargs):
        sent.append(input)
        out = '{"premise": true, "acts": true}' if "--json" in argv else "Each makes 30.\nQUANTITY: 30"
        return SimpleNamespace(returncode=0, stdout=out, stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    return sent


def test_show_prints_the_system_prompt_and_the_prompt(capsys):
    main(["show", "consistent", "same", "2"])
    p = REGISTRY.render(Condition({"disclosure": "same"}), 2)
    assert capsys.readouterr().out == f"[system] {p.system}\n\n{p.user}\n"


def test_list_names_each_lens_and_its_conditions(capsys):
    main(["list"])
    out = capsys.readouterr().out
    assert all(name in out for name in REGISTRY.lenses)
    assert "hubjoint" in out and "disclosure=hub" in out and "ask=joint" in out


def test_run_logs_each_call_to_the_out_file(tmp_path, claude):
    out = tmp_path / "smoke.jsonl"
    main(
        [
            "run",
            "consistent",
            "--conditions",
            "same",
            "--models",
            "haiku",
            "--ns",
            "2",
            "--samples",
            "2",
            "--out",
            str(out),
        ]
    )
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert [(r["condition"], r["sample"], r["value"]) for r in rows] == [("same", 0, 30.0), ("same", 1, 30.0)]
    assert len(claude) == 2


@pytest.mark.parametrize(
    "args, message",
    [(["--conditions", "telepathy"], "telepathy"), (["--ns", "11"], "Cournot takes 1 to 10 firms, not 11")],
)
def test_run_refuses_a_cell_that_cant_run_before_any_call(tmp_path, claude, capsys, args, message):
    with pytest.raises(SystemExit) as e:
        main(["run", "consistent", "--models", "haiku", "--out", str(tmp_path / "r.jsonl"), *args])
    assert message in str(e.value.code) + capsys.readouterr().err
    assert claude == []


def test_an_unknown_lens_is_refused(capsys):
    with pytest.raises(SystemExit):
        main(["show", "charisma", "same", "2"])
    assert "charisma" in capsys.readouterr().err


def test_judge_then_table(tmp_path, claude, capsys):
    out = tmp_path / "smoke.jsonl"
    main(
        [
            "run",
            "consistent",
            "--conditions",
            "same",
            "--models",
            "haiku",
            "--ns",
            "2",
            "--samples",
            "1",
            "--out",
            str(out),
        ]
    )
    main(["judge", "consistent", "--log", str(out)])
    assert (tmp_path / "judge-copy.jsonl").exists()
    capsys.readouterr()
    main(["table", "consistent", "--log", str(out)])
    table = capsys.readouterr().out
    assert "| same | haiku | 2 | 1 | 1 |" in table and "| 1 | 100 |" in table


def test_synth_reads_every_lens_log(tmp_path, claude, capsys, monkeypatch):
    monkeypatch.setattr("zerocommcartel.logs.LOGS", tmp_path)
    main(
        [
            "run",
            "capable",
            "--conditions",
            "same",
            "hubjoint",
            "--models",
            "haiku",
            "--ns",
            "2",
            "--samples",
            "1",
        ]
    )
    capsys.readouterr()
    main(["synth"])
    assert "| haiku | 2 | 1/1 | 1/1 |" in capsys.readouterr().out
