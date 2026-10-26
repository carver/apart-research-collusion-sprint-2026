"""The paper's staging-probe source, on fixture rows (no test reads the probe's log): which answers it counts,
what counts as calling the prompt an evaluation, and its cells; and that the probed prompts it counts are the
prompts the experiments ran."""

import importlib.util

import pytest

from paper.data.staging import PROMPTS, answers, called_evaluation
from zerocommcartel.criteria import REGISTRY


def row(
    wording="salt", model="opus", pq="eval_yn", rep=0, label="YES", value=1.0, reply="<label>YES</label>"
):
    return {
        "wording": wording,
        "model": model,
        "pq": pq,
        "rep": rep,
        "label": label,
        "eval": value,
        "reply": reply,
        "error": None if reply else "timed out",
    }


def test_a_count_takes_the_binary_answers_about_the_prompts_its_market_ran():
    rows = [
        row(),
        row(wording="salt_plain", pq="purpose", label="ASSESSMENT"),
        row(wording="solvent"),
        row(wording="salt_hospitals"),  # a candidate wording no experiment ran
        row(wording="market"),  # the earlier three-firm market
        row(pq="likelihood", label="90", value=0.9),  # the probe's own question
        row(reply=None, label=None, value=0.5),  # a call that failed
        row(model="nemotron"),  # a model no result reports
    ]
    assert [(r["wording"], r["pq"]) for r in answers(rows, 2)] == [
        ("salt", "eval_yn"),
        ("salt_plain", "purpose"),
    ]
    assert [r["wording"] for r in answers(rows, 3)] == ["solvent"]


def test_each_market_counts_the_models_its_results_report():
    rows = [row(model=m) for m in ("haiku", "sonnet", "opus", "astra", "glm")]
    assert [r["model"] for r in answers(rows, 2)] == ["haiku", "sonnet", "opus", "astra", "glm"]
    assert [r["model"] for r in answers(rows, 3)] == []
    rows = [row(wording="solvent", model=m) for m in ("haiku", "sonnet", "opus", "astra", "glm")]
    assert [r["model"] for r in answers(rows, 3)] == ["opus", "astra", "glm"]


def test_an_answer_calls_the_prompt_an_evaluation_only_with_the_evaluation_option():
    assert called_evaluation(row(label="YES", value=1.0))
    assert not called_evaluation(row(label="NO", value=0.0))
    assert not called_evaluation(row(label=None, value=0.5))  # unparsed


def test_a_cell_is_one_model_asked_one_question_about_one_wording():
    rows = [row(rep=0), row(rep=1), row(pq="purpose"), row(wording="salt_plain"), row(model="haiku")]
    cells = [(r["model"], r["prompt_hash"]) for r in answers(rows, 2)]
    assert len(set(cells)) == 4
    assert cells[0] == cells[1]


@pytest.fixture(scope="module")
def probed():
    spec = importlib.util.spec_from_file_location("staging_probe", "experiments/staging_probe.py")
    assert spec and spec.loader
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    return script.wordings()


def test_each_counted_prompt_is_the_one_its_experiment_ran(probed):
    assert set(PROMPTS) == {"salt", "salt_plain", "solvent"}
    for wording, probe in PROMPTS.items():
        prompt = REGISTRY.render(REGISTRY.condition(probe.criterion, probe.condition), probe.firms)
        assert probed[wording] == (prompt.system, prompt.user), wording
