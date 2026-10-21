"""Pacing each model's requests to the rate its provider takes, learned from the provider's refusals.

A model starts with no limit. When OpenRouter refuses a request with HTTP 429 because the model is
over its limit, the refusal's body says how many requests a minute the model takes and when the
minute's count resets. Every request for that model in the process then waits for the reset, and
from then on at most that many go in any minute. The refused request is retried after the wait, up to
``RETRIES`` times, before its agent's turn fails.
"""

import asyncio
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.models.wrapper import WrapperModel
from pydantic_ai.settings import ModelSettings

WINDOW = 60.0  # seconds: OpenRouter limits requests a minute
RETRIES = 4
CLOCK_MARGIN = 1.0  # seconds past a reset, in case this clock is ahead of the provider's
NO_RESET_WAIT = 15.0  # seconds, after a refusal that gives no reset, such as an upstream provider's
MAX_WAIT = 120.0  # seconds; a refusal that asks for longer (a daily cap) fails at once


@dataclass(frozen=True)
class Refusal:
    """What an HTTP 429 asks: ``wait`` seconds, and at most ``per_minute`` requests a minute after
    that, if it says."""

    wait: float
    per_minute: int | None = None

    @classmethod
    def of(cls, error: ModelHTTPError) -> "Refusal":
        """Read OpenRouter's ``X-RateLimit-*`` headers, which it puts in the body's metadata."""
        headers = body_headers(error.body)
        reset = positive_int(headers.get("x-ratelimit-reset"))  # epoch milliseconds
        wait = NO_RESET_WAIT if reset is None else max(reset / 1000 - time.time(), 0.0) + CLOCK_MARGIN
        return cls(wait, positive_int(headers.get("x-ratelimit-limit")))


def positive_int(value: object) -> int | None:
    """``value`` as a whole number above 0, or None if it isn't one."""
    try:
        number = int(str(value))
    except ValueError:
        return None
    return number if number > 0 else None


def body_headers(body: object) -> dict[str, object]:
    """The headers OpenRouter puts in an error body's metadata, by lowercased name."""
    metadata = body.get("metadata") if isinstance(body, dict) else None
    headers = metadata.get("headers") if isinstance(metadata, dict) else None
    return {str(name).lower(): value for name, value in headers.items()} if isinstance(headers, dict) else {}


class RateLimit:
    """One model's pace, shared by every run and agent that uses the model: no limit until a refusal
    sets one."""

    def __init__(self) -> None:
        self.per_minute: int | None = None
        self.paused_until = 0.0  # in the event loop's time
        self.sent: deque[float] = deque()  # when the requests of the last minute went

    async def wait(self) -> None:
        """Wait until the model may take another request, and count it."""
        loop = asyncio.get_running_loop()
        while True:
            now = loop.time()
            while self.sent and self.sent[0] <= now - WINDOW:
                self.sent.popleft()
            if now < self.paused_until:
                await asyncio.sleep(self.paused_until - now)
            elif self.per_minute is not None and len(self.sent) >= self.per_minute:
                await asyncio.sleep(self.sent[0] + WINDOW - now)
            else:
                self.sent.append(now)
                return

    def slow_down(self, refusal: Refusal) -> None:
        """Hold every request until the ``refusal``'s wait is over, and from then on keep to the
        model's limit if the refusal gives it. The provider may have counted requests this process
        didn't make, so the wait holds even when this process's count says there's room."""
        if refusal.per_minute is not None:
            self.per_minute = refusal.per_minute
        self.paused_until = max(self.paused_until, asyncio.get_running_loop().time() + refusal.wait)


class RateLimited(WrapperModel):
    """A model whose requests wait on its ``limit``, and whose refusals (HTTP 429) are retried."""

    def __init__(self, wrapped: Model, limit: RateLimit) -> None:
        super().__init__(wrapped)
        self.limit = limit

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        retries = 0
        while True:
            await self.limit.wait()
            try:
                return await self.wrapped.request(messages, model_settings, model_request_parameters)
            except ModelHTTPError as error:
                refusal = Refusal.of(error) if error.status_code == 429 else None
                if refusal is None or refusal.wait > MAX_WAIT or retries == RETRIES:
                    raise
                retries += 1
                print(
                    f"[{self.model_name}] refused (HTTP 429), retrying in {refusal.wait:.0f}s",
                    file=sys.stderr,
                )
                self.limit.slow_down(refusal)


LIMITS: defaultdict[str, RateLimit] = defaultdict(RateLimit)  # per model name, for the whole process


def paced(model: Model) -> RateLimited:
    """``model``, sharing one pace with every other model of its name in the process."""
    return RateLimited(model, LIMITS[model.model_name])
