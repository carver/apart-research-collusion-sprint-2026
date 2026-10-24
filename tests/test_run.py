"""The runner, with a fake model: what it logs, what a rerun skips and retries, and a log cut short by a
killed run. No test calls a model."""

import json
import time

import pytest

from zerocommcartel import call
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criterion import Criterion, build
from zerocommcartel.logs import load_rows
from zerocommcartel.prompt import Condition, Level, Slot
from zerocommcartel.run import done_keys, plan, run


def answer(reply="QUANTITY: 30"):
    calls = []

    def call(model, system, user):
        calls.append((model, system, user))
        return reply, {"provider": "fake"}

    call.calls = calls
    return call


def tasks(out, conditions=("base", "same"), ns=(2,), samples=2, registry=REGISTRY):
    return plan(registry, "consistent", conditions, ["haiku"], ns, samples, done_keys(load_rows(out)))


def test_a_row_per_call_with_its_cell_and_its_answer(tmp_path):
    out = tmp_path / "consistent" / "results.jsonl"
    assert run(tasks(out, conditions=["same"], samples=1), out, answer("Each makes 30.\nQUANTITY: 30")) == (
        1,
        0,
    )
    (row,) = load_rows(out)
    assert row | {"t": 0, "seconds": 0} == row | {
        "model": "haiku",
        "model_id": "claude-haiku-5-5",
        "criterion": "consistent",
        "condition": "same",
        "levels": {"disclosure": "same"},
        "ask": "own",
        "game": "cournot",
        "game_params": {"a": 130, "c": 10},
        "n": 2,
        "sample": 0,
        "prompt_hash": REGISTRY.render(Condition({"disclosure": "same"}), 2).hash,
        "reply": "Each makes 30.\nQUANTITY: 30",
        "answer": "QUANTITY",
        "value": 30.0,
        "text": None,
        "error": None,
        "provider": "fake",
        "t": 0,
        "seconds": 0,
    }


def test_the_model_gets_the_rendered_prompt(tmp_path):
    call = answer()
    run(tasks(tmp_path / "r.jsonl", conditions=["same"], samples=1), tmp_path / "r.jsonl", call)
    p = REGISTRY.render(Condition({"disclosure": "same"}), 2)
    assert call.calls == [("haiku", p.system, p.user)]


def test_a_rerun_asks_only_for_what_is_missing(tmp_path):
    out = tmp_path / "r.jsonl"
    run(tasks(out, samples=2), out, answer())
    assert tasks(out, samples=2) == []
    assert [(t.name, t.sample) for t in tasks(out, samples=3)] == [("base", 2), ("same", 2)]


def test_a_failed_call_is_logged_and_retried_by_the_next_run(tmp_path):
    out = tmp_path / "r.jsonl"

    def fail(model, system, user):
        raise RuntimeError("rate limited")

    assert run(tasks(out, conditions=["same"], samples=1), out, fail) == (0, 1)
    (row,) = load_rows(out)
    assert (row["reply"], row["value"], row["error"]) == (None, None, "rate limited")
    assert len(tasks(out, conditions=["same"], samples=1)) == 1


def test_a_reworded_condition_is_a_new_cell(tmp_path):
    out = tmp_path / "r.jsonl"
    old = build([Criterion("consistent", "?", conditions={"x": Condition({"disclosure": "anyai"})})])
    new = build([Criterion("consistent", "?", conditions={"x": Condition({"disclosure": "samemodel"})})])
    run(tasks(out, conditions=["x"], samples=1, registry=old), out, answer())
    assert tasks(out, conditions=["x"], samples=1, registry=old) == []
    assert len(tasks(out, conditions=["x"], samples=1, registry=new)) == 1


def test_a_line_cut_short_by_a_killed_run_is_skipped_and_the_next_row_starts_its_own_line(tmp_path, capsys):
    out = tmp_path / "r.jsonl"
    run(tasks(out, conditions=["same"], samples=1), out, answer())
    with out.open("a") as f:
        f.write('{"model": "haiku", "prompt_ha')
    rows = load_rows(out)
    assert len(rows) == 1 and "skipped 1 unreadable line" in capsys.readouterr().err
    run(tasks(out, conditions=["base"], samples=1), out, answer())
    assert [r["condition"] for r in load_rows(out)] == ["same", "base"]
    assert json.loads(out.read_text().splitlines()[-1])["condition"] == "base"


def test_a_missing_log_has_no_rows(tmp_path):
    assert load_rows(tmp_path / "none.jsonl") == []


@pytest.mark.parametrize(
    "conditions, models, ns, match",
    [
        (["telepathy"], ["haiku"], [2], "telepathy"),
        (["same"], ["gpt-9"], [2], "gpt-9"),
        (["same"], ["haiku"], [11], "11"),
    ],
)
def test_an_unknown_condition_model_or_market_size_is_refused_before_any_call(conditions, models, ns, match):
    with pytest.raises(ValueError, match=match):
        plan(REGISTRY, "consistent", conditions, models, ns, 1)


def test_a_question_the_market_size_cant_take_is_refused_before_any_call():
    registry = build([Criterion("consistent", "?", conditions={"fc": Condition(ask="forecast")})])
    with pytest.raises(ValueError, match="n = 1"):
        plan(registry, "consistent", ["base", "fc"], ["haiku"], [2, 1], 1)


def test_a_prompt_that_names_the_model_is_rendered_for_each_model(tmp_path):
    named = Slot("context", {"none": Level(), "on": Level("Rivals ask {model}.")})
    named_condition = {"m": Condition({"named": "on"})}
    reg = build([Criterion("consistent", "?", slots={"named": named}, conditions=named_condition)])
    call = answer()
    run(plan(reg, "consistent", ["m"], ["haiku", "opus"], [2], 1), tmp_path / "r.jsonl", call)
    asked = {model: user for model, _, user in call.calls}
    assert "Rivals ask Claude Haiku 5.5." in asked["haiku"] and "Rivals ask Claude Opus 5.5." in asked["opus"]


def test_a_row_records_the_id_its_call_was_routed_to(tmp_path, monkeypatch):
    monkeypatch.setattr("zerocommcartel.call.codex_ready", lambda: False)
    out = tmp_path / "r.jsonl"
    run(plan(REGISTRY, "consistent", ["same"], ["astra"], [2], 1), out, answer())
    assert [r["model_id"] for r in load_rows(out)] == ["openai/gpt-6-astra"]


def test_a_run_checks_codex_once_however_many_threads_start_at_once(tmp_path, monkeypatch, capsys):
    looked = []

    def slow_which(name):
        looked.append(name)
        time.sleep(0.2)
        return None

    monkeypatch.setattr(call.shutil, "which", slow_which)
    call.codex_ready.cache_clear()
    astra = plan(REGISTRY, "consistent", ["base"], ["astra"], [2], 8)
    run(astra, tmp_path / "out.jsonl", answer(), workers=8)
    call.codex_ready.cache_clear()
    assert looked == ["codex"] and capsys.readouterr().err.count("Codex isn't installed") == 1
