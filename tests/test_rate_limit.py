import asyncio
import time
from collections.abc import Callable
from functools import partial

import pytest
import virtual_time
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import FunctionModel

from tradingcartel.agents.llm import AgentTurn, LLMAgent
from tradingcartel.agents.rate_limit import RateLimit, RateLimited

MODEL = "fake/model"


def over_limit(reset_in: float, per_minute: int | None = 20) -> ModelHTTPError:
    """OpenRouter's refusal of a request over the model's ``per_minute`` limit (None: the refusal
    doesn't say it), as its body comes: the count resets in ``reset_in`` seconds."""
    reset = round((time.time() + reset_in) * 1000)
    headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset)}
    if per_minute is not None:
        headers["X-RateLimit-Limit"] = str(per_minute)
    message = f"Rate limit exceeded: new-account-rpm/{MODEL}. Rate limit reached: new accounts are limited."
    body = {"message": message, "code": 429, "metadata": {"headers": headers, "provider_name": None}}
    return ModelHTTPError(429, MODEL, body)


def upstream() -> ModelHTTPError:
    """An upstream provider's refusal, which OpenRouter passes on with no reset."""
    raw = f"{MODEL} is temporarily rate-limited upstream."
    body = {
        "message": "Provider returned error",
        "code": 429,
        "metadata": {"raw": raw, "provider_name": "Fake"},
    }
    return ModelHTTPError(429, MODEL, body)


class Server:
    """A fake OpenRouter model that takes ``per_minute`` requests in each minute of the loop's clock
    and refuses the rest the way OpenRouter does. It already counts ``elsewhere`` requests from
    another client in the first minute. An answer takes ``seconds``. ``accepted`` and ``refused``
    hold the times this client's requests came in."""

    def __init__(self, per_minute: int = 20, seconds: float = 3.0, elsewhere: int = 0) -> None:
        self.per_minute = per_minute
        self.seconds = seconds
        self.elsewhere = elsewhere
        self.accepted: list[float] = []
        self.refused: list[float] = []
        self.model = FunctionModel(self.respond, model_name=MODEL)

    async def respond(self, messages, info) -> ModelResponse:
        now = asyncio.get_running_loop().time()
        minute = now // 60
        counted = sum(t // 60 == minute for t in self.accepted) + (self.elsewhere if minute == 0 else 0)
        if counted >= self.per_minute:
            self.refused.append(now)
            raise over_limit(reset_in=(minute + 1) * 60 - now, per_minute=self.per_minute)
        self.accepted.append(now)
        await asyncio.sleep(self.seconds)
        return ModelResponse(parts=[TextPart("ok")])


class Refuses:
    """A fake model that refuses its first requests, one for each of ``refusals``, with the error it
    makes at that moment, and answers the rest at once. ``arrivals`` holds the time each request came
    in."""

    def __init__(self, *refusals: Callable[[], ModelHTTPError]) -> None:
        self.refusals = list(refusals)
        self.arrivals: list[float] = []
        self.model = FunctionModel(self.respond, model_name=MODEL)

    async def respond(self, messages, info) -> ModelResponse:
        self.arrivals.append(asyncio.get_running_loop().time())
        if self.refusals:
            raise self.refusals.pop(0)()
        return ModelResponse(parts=[TextPart("ok")])


async def turns(model: Model, count: int, start: float = 0.0) -> list[AgentTurn]:
    """The records of an agent's ``count`` turns on ``model``, one request each, from ``start``."""
    await asyncio.sleep(start)
    agent = LLMAgent("subject", model, "", [])
    records = []

    async def submit(message):
        records.append(message)
        return []

    for _ in range(count):
        await agent.act("Go.", submit)
    return records


async def parallel_runs(model: Model, runs: int, count: int) -> list[AgentTurn]:
    """The records of ``runs`` runs' turns, ``count`` each, started half a second apart. Their models
    share one limit, as every run of a model in a sweep does."""
    limit = RateLimit()
    started = (turns(RateLimited(model, limit), count, start=i / 2) for i in range(runs))
    return [turn for run in await asyncio.gather(*started) for turn in run]


def test_parallel_runs_of_a_model_wait_their_turn_once_a_refusal_says_its_limit():
    server = Server(per_minute=20, seconds=3)

    records = virtual_time.run(parallel_runs(server.model, runs=4, count=15))

    assert [turn.error for turn in records if turn.error] == []
    assert len(server.accepted) == 60
    assert len(server.refused) == 1
    assert max(server.accepted) < 180  # 20 a minute, and no slower


def test_a_refusal_holds_back_every_run_until_the_reset_though_the_provider_counted_more():
    server = Server(per_minute=20, seconds=3, elsewhere=18)

    records = virtual_time.run(parallel_runs(server.model, runs=4, count=5))

    assert [turn.error for turn in records if turn.error] == []
    assert len(server.refused) == 1
    assert min(t for t in server.accepted if t > 2) == pytest.approx(61, abs=0.1)


def test_a_refused_request_is_retried_after_the_reset_and_a_second_more():
    model = Refuses(partial(over_limit, reset_in=30))

    [turn] = virtual_time.run(turns(RateLimited(model.model, RateLimit()), 1))

    assert turn.error is None
    assert model.arrivals == pytest.approx([0, 31], abs=0.1)


def test_a_request_refused_every_time_fails_its_turn_after_four_retries():
    model = Refuses(*[partial(over_limit, reset_in=30)] * 6)

    [turn] = virtual_time.run(turns(RateLimited(model.model, RateLimit()), 1))

    assert turn.error is not None and "429" in turn.error
    assert model.arrivals == pytest.approx([0, 31, 62, 93, 124], abs=0.1)


def test_an_upstream_refusal_with_no_reset_is_retried_after_fifteen_seconds():
    model = Refuses(upstream)

    [turn] = virtual_time.run(turns(RateLimited(model.model, RateLimit()), 1))

    assert turn.error is None
    assert model.arrivals == pytest.approx([0, 15], abs=0.1)


def test_a_refusal_with_a_reset_but_no_limit_still_waits_for_the_reset():
    model = Refuses(partial(over_limit, reset_in=30, per_minute=None))

    [turn] = virtual_time.run(turns(RateLimited(model.model, RateLimit()), 1))

    assert turn.error is None
    assert model.arrivals == pytest.approx([0, 31], abs=0.1)


def test_a_limit_below_one_leaves_the_model_unlimited_after_the_reset():
    model = Refuses(partial(over_limit, reset_in=30, per_minute=0))

    records = virtual_time.run(turns(RateLimited(model.model, RateLimit()), 3))

    assert [turn.error for turn in records] == [None, None, None]
    assert model.arrivals == pytest.approx([0, 31, 31, 31], abs=0.1)


def test_a_refusal_whose_reset_is_far_off_fails_its_turn_at_once_and_holds_back_nothing():
    model = Refuses(partial(over_limit, reset_in=3600))  # a daily cap
    limited = RateLimited(model.model, RateLimit())

    failed, answered = virtual_time.run(turns(limited, 2))

    assert failed.error is not None and "429" in failed.error
    assert answered.error is None
    assert model.arrivals == [0, 0]


def test_other_errors_fail_the_turn_without_a_retry():
    model = Refuses(lambda: ModelHTTPError(402, MODEL, {"message": "Insufficient credits", "code": 402}))

    [turn] = virtual_time.run(turns(RateLimited(model.model, RateLimit()), 1))

    assert turn.error is not None and "402" in turn.error
    assert model.arrivals == [0]
