"""An experiment's script, with a fake model and a fake judge: the calls it counts, makes and skips, its fresh
logs, its judges, its report, and the OpenRouter key it reads from .env. No test calls a model."""

import re

import pytest

from zerocommcartel.experiment import Experiment, load_env, main
from zerocommcartel.logs import load_rows


@pytest.fixture(autouse=True)
def codex_ready(monkeypatch):
    """No test asks the real Codex whether it's logged in."""
    monkeypatch.setattr("zerocommcartel.call.codex_ready", lambda: True)


EXP = Experiment(
    "CAP-1",
    "Joint optimum",
    "capable",
    conditions=("joint", "joint_default"),
    models=("opus", "astra"),
    ns=(3,),
    samples=2,
    judges=("working",),
    report=lambda replies: f"{len(replies.rows)} replies reported",
)


def model(model, system, user):
    return "Each firm makes 20.\nDECISION: 20", {}


def judge(judge, prompt):
    return '{"derives": true, "joint_per_firm": 20, "declines": false}'


def test_an_experiment_counts_its_calls():
    assert EXP.calls == 8


def test_a_dry_run_counts_the_calls_and_makes_none(tmp_path, capsys):
    made = []
    main(EXP, ["--dry-run", "--log", str(tmp_path / "r.jsonl")], call=lambda *a: made.append(a))
    out = capsys.readouterr().out
    assert "CAP-1 Joint optimum: 2 models x 2 conditions x 1 market size x 2 samples = 8 calls" in out
    assert "8 to make" in out
    assert made == [] and not (tmp_path / "r.jsonl").exists()


def test_the_script_says_where_each_models_calls_go_before_making_any(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("zerocommcartel.call.codex_ready", lambda: False)
    main(EXP, ["--dry-run", "--log", str(tmp_path / "r.jsonl")])
    routes = "routes: opus claude-opus-5-5 (claude), astra openai/gpt-6-astra (openrouter)"
    assert routes in capsys.readouterr().out


def test_a_run_makes_the_missing_calls_then_judges_and_reports(tmp_path, capsys):
    log = tmp_path / "r.jsonl"
    main(EXP, ["--log", str(log)], call=model, judge_call=judge)
    assert len(load_rows(log)) == 8
    assert len(load_rows(tmp_path / "judge-working.jsonl")) == 1  # the eight replies are one text
    assert capsys.readouterr().out.rstrip().endswith("8 replies reported")
    main(EXP, ["--log", str(log)], call=model, judge_call=judge)
    assert len(load_rows(log)) == 8
    assert "0 to make" in capsys.readouterr().out


def test_each_experiment_logs_to_a_folder_of_its_own_in_its_criterions(tmp_path, monkeypatch):
    monkeypatch.setattr("zerocommcartel.logs.LOGS", tmp_path)
    main(EXP, [], call=model, judge_call=judge)
    assert len(load_rows(tmp_path / "capable" / "cap1" / "results.jsonl")) == 8
    assert (tmp_path / "capable" / "cap1" / "judge-working.jsonl").exists()
    assert not (tmp_path / "capable" / "results.jsonl").exists()


def test_fresh_makes_every_call_again_in_a_new_dated_log(tmp_path, monkeypatch):
    monkeypatch.setattr("zerocommcartel.logs.LOGS", tmp_path)
    main(EXP, [], call=model, judge_call=judge)
    main(EXP, ["--fresh"], call=model, judge_call=judge)
    fresh = list((tmp_path / "capable" / "cap1").glob("results-*.jsonl"))
    dated = r"results-\d{4}-\d{2}-\d{2}-\d{4}\.jsonl"
    assert [re.fullmatch(dated, f.name) is not None for f in fresh] == [True]
    assert len(load_rows(fresh[0])) == 8


def test_the_report_can_read_another_experiments_log_without_running_it(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("zerocommcartel.logs.LOGS", tmp_path)
    base = Experiment(**{**EXP.__dict__, "id": "BASELINES", "conditions": ("joint_default",), "judges": ()})
    main(base, [], call=model, judge_call=judge)
    beside = Experiment(**{**EXP.__dict__, "conditions": ("joint",), "compare": ("capable/baselines",)})
    capsys.readouterr()
    main(beside, [], call=model, judge_call=judge)
    out = capsys.readouterr().out
    assert "4 to make" in out and out.rstrip().endswith("8 replies reported")
    assert len(load_rows(tmp_path / "capable" / "cap1" / "results.jsonl")) == 4


def test_the_report_sees_only_the_experiments_own_cells(tmp_path, capsys):
    log = tmp_path / "r.jsonl"
    other = Experiment(**{**EXP.__dict__, "conditions": ("joint",), "models": ("opus",)})
    main(other, ["--log", str(log)], call=model, judge_call=judge)
    main(EXP, ["--log", str(log)], call=model, judge_call=judge)
    capsys.readouterr()
    main(other, ["--log", str(log)], call=model, judge_call=judge)
    assert capsys.readouterr().out.rstrip().endswith("2 replies reported")


def test_the_openrouter_key_comes_from_dotenv_only_when_it_isnt_set(tmp_path):
    dotenv = tmp_path / ".env"
    dotenv.write_text('# keys\nOPENROUTER_API_KEY="sk-from-file"\nOTHER_KEY=x\n')
    unset: dict[str, str] = {}
    load_env(dotenv, unset)
    already = {"OPENROUTER_API_KEY": "sk-set"}
    load_env(dotenv, already)
    nothing: dict[str, str] = {}
    load_env(tmp_path / "missing.env", nothing)
    assert unset == {"OPENROUTER_API_KEY": "sk-from-file"}
    assert (already, nothing) == ({"OPENROUTER_API_KEY": "sk-set"}, {})


def test_rows_read_from_another_experiment_bring_their_judges_labels(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("zerocommcartel.logs.LOGS", tmp_path)

    def by_round(model, system, user):
        return f"{'After a round.' if 'round 2' in user else 'First round.'}\nDECISION: 20", {}

    base = Experiment(**{**EXP.__dict__, "id": "BASELINES", "conditions": ("joint_default",)})
    main(base, [], call=by_round, judge_call=judge)

    def labelled(replies):
        return f"{sum('working' in r['labels'] for r in replies.rows)} labelled"

    beside = Experiment(
        **{**EXP.__dict__, "conditions": ("joint",), "compare": ("capable/baselines",), "report": labelled}
    )
    capsys.readouterr()
    main(beside, [], call=by_round, judge_call=judge)
    assert capsys.readouterr().out.rstrip().endswith("8 labelled")
