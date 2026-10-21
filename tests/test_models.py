from collections import defaultdict

from pydantic_ai.models.openrouter import OpenRouterModel

from tradingcartel.agents import rate_limit
from tradingcartel.agents.llm import make_model
from tradingcartel.agents.rate_limit import RateLimit, RateLimited


def test_openrouter_models_report_cost_and_can_cap_reasoning(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "unused")

    model = make_model("openai/gpt-5", reasoning_effort="low")

    assert model.settings["openrouter_usage"] == {"include": True}
    assert model.settings["openrouter_reasoning"] == {"effort": "low"}


def test_reasoning_is_left_to_the_provider_by_default(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "unused")

    assert "openrouter_reasoning" not in make_model("openai/gpt-5").settings


def test_openrouter_models_share_one_rate_limit_per_model_and_others_have_none(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "unused")
    monkeypatch.setattr(rate_limit, "LIMITS", defaultdict(RateLimit))

    sol, sol_low = make_model("openai/gpt-6.1-sol"), make_model("openai/gpt-6.1-sol", "low")
    grok = make_model("x-ai/grok-4.7")

    assert isinstance(sol, RateLimited) and isinstance(sol_low, RateLimited) and isinstance(grok, RateLimited)
    assert isinstance(sol.wrapped, OpenRouterModel)
    assert sol.limit is sol_low.limit and sol.limit is not grok.limit
    assert not isinstance(make_model("claude-cli:haiku"), RateLimited)
    assert not isinstance(make_model("test"), RateLimited)
