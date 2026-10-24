"""The zcc command line. claude-fresh is faked (subprocess.run), so no test calls a model."""

import json
import subprocess
from types import SimpleNamespace

import pytest

from zerocommcartel.cli import main
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criterion import Criterion, build
from zerocommcartel.judge import COPY, Judge
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


def test_table_shows_only_the_conditions_and_models_asked_for(tmp_path, claude, capsys):
    out = tmp_path / "smoke.jsonl"
    run_haiku("consistent", "same", "base", out=out)
    run_haiku("consistent", "same", out=out, model="sonnet")
    (base,) = [row for row in map(json.loads, out.read_text().splitlines()) if row["condition"] == "base"]
    with out.open("a") as f:  # a failed call in a cell the table leaves out
        f.write(json.dumps({**base, "reply": None, "sample": 5, "error": "rate limited"}) + "\n")
    table = table_of(capsys, "consistent", "--log", out, "--conditions", "same", "--models", "haiku")
    assert "| same | haiku | 2 |" in table
    assert "| base |" not in table and "| sonnet |" not in table
    assert "failed" not in table


def test_the_filter_reaches_the_baseline_rows_borrowed_from_another_criterion(logs_dir, claude, capsys):
    run_haiku("capable", "same")
    assert "| same | haiku | 2 |" in table_of(capsys, "consistent", "--conditions", "same")
    assert "| same |" not in table_of(capsys, "consistent", "--conditions", "same", "--models", "sonnet")


def test_a_filter_that_matches_nothing_says_so(tmp_path, claude, capsys):
    out = tmp_path / "smoke.jsonl"
    run_haiku("consistent", "same", out=out)
    assert "No replies match" in table_of(capsys, "consistent", "--log", out, "--models", "sonnet")


@pytest.mark.parametrize(
    "argv, name", [(["--conditions", "telepathy"], "telepathy"), (["--models", "gpt-9"], "gpt-9")]
)
def test_table_refuses_a_condition_or_model_it_doesnt_know(tmp_path, capsys, argv, name):
    with pytest.raises(SystemExit) as e:
        zcc("table", "consistent", "--log", tmp_path / "none.jsonl", *argv)
    assert name in str(e.value.code) + capsys.readouterr().err


def test_synth_reads_every_criterion_log_and_counts_a_baseline_reply_once(logs_dir, claude, capsys):
    run_haiku("capable", "same", "joint", n=3)
    capsys.readouterr()
    main(["synth"])
    # same answers 30 against the cartel's 20; joint answers 20
    assert "| haiku | 3 | 0/1 | - | 1/1 |" in capsys.readouterr().out


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    """Every criterion's own log under tmp_path."""
    monkeypatch.setattr("zerocommcartel.logs.LOGS", tmp_path)
    return tmp_path


def zcc(*argv):
    main([str(a) for a in argv])


def run_haiku(criterion, *conditions, n=2, samples=1, out=None, model="haiku"):
    zcc(
        "run", criterion, "--conditions", *conditions, "--models", model, "--ns", n, "--samples", samples,
        *(["--out", out] if out else []),
    )  # fmt: skip


def table_of(capsys, criterion, *argv):
    capsys.readouterr()
    zcc("table", criterion, *argv)
    return capsys.readouterr().out


def test_a_criterions_table_counts_the_baseline_replies_another_criterion_logged(logs_dir, claude, capsys):
    run_haiku("communal", "same", "base")
    table = table_of(capsys, "consistent")
    assert "| same | haiku | 2 | 1 | 1 |" in table and "| base | haiku | 2 | 1 | 1 |" in table


def test_only_the_baseline_is_shared(logs_dir, claude, capsys):
    run_haiku("communal", "last_diff")
    table = table_of(capsys, "consistent")
    assert "last_diff" not in table and "older wording" not in table


def test_run_skips_a_baseline_sample_another_criterion_logged(logs_dir, claude):
    run_haiku("communal", "same")
    run_haiku("consistent", "same", samples=2)
    assert len(claude) == 2
    rows = [json.loads(line) for line in (logs_dir / "consistent" / "results.jsonl").read_text().splitlines()]
    assert [r["sample"] for r in rows] == [1]


def test_where_two_logs_hold_one_sample_the_criterions_own_reply_counts(logs_dir, claude, capsys):
    run_haiku("communal", "same")
    (theirs,) = [
        json.loads(line) for line in (logs_dir / "communal" / "results.jsonl").read_text().splitlines()
    ]
    mine = theirs | {"criterion": "consistent", "reply": "QUANTITY: 40", "value": 40.0}
    (logs_dir / "consistent").mkdir()
    (logs_dir / "consistent" / "results.jsonl").write_text(json.dumps(mine) + "\n")
    assert "| same | haiku | 2 | 1 | 1 | 40 |" in table_of(capsys, "consistent")


def test_a_log_given_on_the_command_line_stands_alone(logs_dir, claude, tmp_path, capsys):
    run_haiku("communal", "same")
    run_haiku("consistent", "same", out=tmp_path / "smoke.jsonl")
    assert len(claude) == 2
    assert "| same | haiku |" not in table_of(capsys, "consistent", "--log", tmp_path / "empty.jsonl")


def test_judging_leaves_out_the_replies_another_criterions_cache_labels(logs_dir, claude, capsys):
    run_haiku("communal", "same")
    zcc("judge", "communal")
    zcc("judge", "consistent")
    assert len(claude) == 2  # the reply, and communal's judge call
    assert not (logs_dir / "consistent" / "judge-copy.jsonl").exists()
    table = table_of(capsys, "consistent")
    assert "| same | haiku | 2 | 1 | 1 |" in table and "| 1 | 100 |" in table


def test_judging_labels_only_the_replies_the_tables_count(logs_dir, claude, capsys):
    run_haiku("communal", "same")
    log = logs_dir / "communal" / "results.jsonl"
    (current,) = [json.loads(line) for line in log.read_text().splitlines()]
    older = current | {"prompt_hash": "0ld0ld0ld0ld", "reply": "an older wording\nQUANTITY: 40"}
    log.write_text(log.read_text() + json.dumps(older) + "\n")
    zcc("judge", "consistent")
    assert len(claude) == 2  # the reply, and one judge call for it
    assert "older wording" not in claude[-1]


def experiment_file(logs_dir, criterion, folder, name="results.jsonl"):
    """A log in one of the criterion's experiments' folders, as zerocommcartel.experiment writes it."""
    return logs_dir / criterion / folder / name


def test_a_criterions_table_counts_the_replies_its_experiments_logged(logs_dir, claude, capsys):
    run_haiku("capable", "joint", n=3, out=experiment_file(logs_dir, "capable", "cap1"))
    run_haiku("capable", "symmetry", n=3, out=experiment_file(logs_dir, "capable", "cap2"))
    table = table_of(capsys, "capable")
    assert "| joint | haiku | 3 | 1 | 1 |" in table and "| symmetry | haiku | 3 | 1 | 1 |" in table


def test_a_dated_rerun_beside_an_experiments_log_is_left_out(logs_dir, claude, capsys):
    run_haiku("capable", "joint", n=3, out=experiment_file(logs_dir, "capable", "cap1"))
    rerun = experiment_file(logs_dir, "capable", "cap1", "results-2026-10-23-2116.jsonl")
    run_haiku("capable", "joint", n=3, samples=2, out=rerun)
    assert "| joint | haiku | 3 | 1 | 1 |" in table_of(capsys, "capable")


def test_where_an_experiment_and_the_criterions_own_log_hold_one_sample_its_own_counts(
    logs_dir, claude, capsys
):
    run_haiku("capable", "joint", n=3, samples=2, out=experiment_file(logs_dir, "capable", "cap1"))
    theirs = json.loads(experiment_file(logs_dir, "capable", "cap1").read_text().splitlines()[0])
    mine = theirs | {"reply": "DECISION: 40", "value": 40.0}
    (logs_dir / "capable" / "results.jsonl").write_text(json.dumps(mine) + "\n")
    # 40 and the experiment's other sample's 20, not its 20 twice
    assert "| joint | haiku | 3 | 2 | 2 | 30 |" in table_of(capsys, "capable")


def test_run_skips_a_sample_one_of_the_criterions_experiments_logged(logs_dir, claude):
    run_haiku("capable", "joint", n=3, out=experiment_file(logs_dir, "capable", "cap1"))
    run_haiku("capable", "joint", n=3, samples=2)
    assert len(claude) == 2
    rows = [json.loads(line) for line in (logs_dir / "capable" / "results.jsonl").read_text().splitlines()]
    assert [r["sample"] for r in rows] == [1]


@pytest.mark.parametrize(
    "criterion, folder",
    [("capable", "baselines"), ("compliant", "cpl1")],  # beside the experiment's log; a folder with none
)
def test_judging_leaves_out_the_replies_an_experiments_cache_labels(
    logs_dir, claude, capsys, criterion, folder
):
    run_haiku("capable", "same_prompt", n=3, out=experiment_file(logs_dir, "capable", "baselines"))
    (row,) = map(json.loads, experiment_file(logs_dir, "capable", "baselines").read_text().splitlines())
    cache = experiment_file(logs_dir, criterion, folder, "judge-copy.jsonl")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"key": COPY.key(row["reply"]), "premise": True, "acts": False}) + "\n")
    zcc("judge", "capable")
    assert len(claude) == 1  # the reply; no judge call
    assert not (logs_dir / "capable" / "judge-copy.jsonl").exists()
    table = table_of(capsys, "capable")
    assert "| same_prompt | haiku | 3 | 1 | 1 |" in table and "| 1 | 100 |" in table


def test_a_criterions_table_counts_the_baseline_replies_another_criterions_experiment_logged(
    logs_dir, claude, capsys
):
    run_haiku("capable", "same", "no_info", out=experiment_file(logs_dir, "capable", "cap9"))
    table = table_of(capsys, "consistent")
    assert "| same | haiku | 2 | 1 | 1 |" in table and "no_info" not in table


def test_synth_counts_a_measure_from_the_criterions_experiments(logs_dir, claude, capsys):
    run_haiku("capable", "joint", n=3, out=experiment_file(logs_dir, "capable", "cap1"))
    capsys.readouterr()
    main(["synth"])
    assert "| haiku | 3 | - | - | 1/1 |" in capsys.readouterr().out


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


def test_grid_prints_a_table_per_measure_for_the_market_sizes_asked_for(logs_dir, claude, capsys):
    run_haiku("consistent", "same", n=2)
    run_haiku("consistent", "same", n=4)
    capsys.readouterr()
    zcc("grid", "consistent", "--conditions", "same", "--ns", "2", "--at", "cartel", "--below", "cartel")
    out = capsys.readouterr().out
    assert out.index("at cartel") < out.index("below cartel")
    assert (
        out.count("| same | 2 | 1 of 1 | 1 of 1 |") == 1 and out.count("| same | 2 | 0 of 1 | 0 of 1 |") == 1
    )
    assert "| same | 4 |" not in out


def test_table_shows_only_the_market_sizes_asked_for(logs_dir, claude, capsys):
    run_haiku("consistent", "same", n=2)
    run_haiku("consistent", "same", n=4)
    out = table_of(capsys, "consistent", "--ns", "4")
    assert "| same | haiku | 4 |" in out and "| same | haiku | 2 |" not in out


def test_grid_prints_its_measures_in_the_order_given(logs_dir, claude, capsys):
    run_haiku("consistent", "same", n=2)
    capsys.readouterr()
    zcc(
        "grid", "consistent", "--conditions", "same", "--below", "nash", "--at", "cartel", "--below", "cartel"
    )
    out = capsys.readouterr().out
    assert out.index("below nash") < out.index("at cartel") < out.index("below cartel")


def test_grid_refuses_a_focal_point_no_reply_has_and_names_the_ones_they_do(logs_dir, claude, capsys):
    run_haiku("consistent", "same", n=2)
    with pytest.raises(SystemExit) as e:
        zcc("grid", "consistent", "--conditions", "same", "--at", "carel")
    message = str(e.value.code)
    assert "carel" in message and "cartel" in message and "nash" in message


@pytest.mark.parametrize("out", [None, "smoke.jsonl"])
def test_run_plan_prices_the_calls_from_every_log_and_makes_none(logs_dir, claude, capsys, monkeypatch, out):
    monkeypatch.setattr("zerocommcartel.call.call_openrouter", lambda *a: pytest.fail("called OpenRouter"))
    earlier = logs_dir / "communal" / "results.jsonl"
    earlier.parent.mkdir(parents=True)
    earlier.write_text(json.dumps({"model": "glm", "condition": "base", "cost": 0.005}) + "\n")
    capsys.readouterr()
    plan = ["--conditions", "base", "--models", "haiku", "glm", "--ns", "2", "--samples", "4", "--plan"]
    zcc("run", "consistent", *plan, *(["--out", logs_dir / out] if out else []))
    printed = capsys.readouterr().out
    assert claude == [] and earlier.read_text().count("\n") == 1 and not (logs_dir / "consistent").exists()
    assert "8 calls to make" in printed and "subscription" in printed
    assert "~$0.02 ($0.0050 a call), from earlier calls on each condition" in printed
    assert "OpenRouter: ~$0.02" in printed
