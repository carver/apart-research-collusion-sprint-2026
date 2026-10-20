from pydantic_ai.models.openrouter import OpenRouterModel

from tradingcartel.agents.llm import make_model


def test_openrouter_models_report_cost_and_can_cap_reasoning(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "unused")

    model = make_model("openai/gpt-5", reasoning_effort="low")

    assert isinstance(model, OpenRouterModel)
    assert model.settings["openrouter_usage"] == {"include": True}
    assert model.settings["openrouter_reasoning"] == {"effort": "low"}


def test_reasoning_is_left_to_the_provider_by_default(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "unused")

    assert "openrouter_reasoning" not in make_model("openai/gpt-5").settings
