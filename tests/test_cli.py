"""The zcc command line. claude-fresh is faked (subprocess.run), so no test calls a model."""

import json
import subprocess
from types import SimpleNamespace

import pytest

from zerocommcartel.cli import main
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criterion import Criterion, build
from zerocommcartel.judge import Judge
from zerocommcartel.prompt import Condition


@pytest.fixture
def claude(monkeypatch):
    """The prompts each claude-fresh call gets. Replies say QUANTITY: 30 and DECISION: 20; a judge says yes to
    both labels."""
    sent = []

    def run(argv, input=None, **kwargs):
        sent.append(input)
        reply = "Each makes 30.\nQUANTITY: 30\nDECISION: 20"  # QUANTITY for Cournot, DECISION for the market
        out = '{"premise": true, "acts": true}' if "--json" in argv else reply
        return SimpleNamespace(returncode=0, stdout=out, stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    return sent


def test_show_prints_the_system_prompt_and_the_prompt(capsys):
    main(["show", "consistent", "same", "2"])
    p = REGISTRY.render(Condition({"disclosure": "same"}), 2)
    assert capsys.readouterr().out == f"[system] {p.system}\n\n{p.user}\n"


def test_list_names_each_criterion_and_its_conditions(capsys):
    main(["list"])
    out = capsys.readouterr().out
    assert all(name in out for name in REGISTRY.criteria)
    assert "joint_default" in out and "ask=joint game=repeated" in out


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


def test_an_unknown_criterion_is_refused(capsys):
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


def test_synth_reads_every_criterion_log(tmp_path, claude, capsys, monkeypatch):
    monkeypatch.setattr("zerocommcartel.logs.LOGS", tmp_path)
    main(
        [
            "run",
            "capable",
            "--conditions",
            "same",
            "joint",
            "--models",
            "haiku",
            "--ns",
            "3",
            "--samples",
            "1",
        ]
    )
    capsys.readouterr()
    main(["synth"])
    # same answers 30 against the cartel's 20; joint answers 20
    assert "| haiku | 3 | 0/1 | 1/1 |" in capsys.readouterr().out


def hashes(capsys, *argv, registry=REGISTRY):
    main(["hashes", *argv], registry=registry)
    return capsys.readouterr().out.splitlines()


def test_hashes_gives_a_prompt_the_pilot_sent_the_pilots_hash(capsys):
    lines = hashes(capsys)
    # the pilot's cournot `same` arm at n = 2 and `base` at n = 4, from logs/pilot/probe-results.jsonl
    assert "consistent same 2 e84324d17411" in lines
    assert "capable base 4 1e424d41c4bf" in lines


def test_hashes_covers_the_market_sizes_asked_for_that_the_game_can_take(capsys):
    lines = hashes(capsys, "--ns", "3", "2")
    assert any(line.startswith("capable base 3 ") for line in lines)
    assert not any(line.startswith("capable base 4 ") for line in lines)
    assert any(line.startswith("communal fixed_diff 2 ") for line in lines)
    assert not any(line.startswith("communal fixed_diff 3 ") for line in lines)


def test_a_judge_line_changes_with_that_judge_alone(capsys):
    schema = {"type": "object", "properties": {"harm": {"type": "boolean"}}, "required": ["harm"]}

    def registry(prompt):
        return build([Criterion("a", "?", judges={"harm": Judge("harm", prompt, schema)})])

    old = hashes(capsys, registry=registry("Is it harmful? {reply}"))
    new = hashes(capsys, registry=registry("Does it harm buyers? {reply}"))
    changed = [(a, b) for a, b in zip(old, new, strict=True) if a != b]
    assert [(a.split()[:2], b.split()[:2]) for a, b in changed] == [(["judge", "harm"], ["judge", "harm"])]
    assert any(line.startswith("judge copy ") for line in old)
