"""LLM agents, run with PydanticAI. Real models go through OpenRouter, or through the ``claude -p``
CLI on a Claude subscription (``claude_cli``)."""

import os
import sys
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pydantic_ai
from pydantic import Field
from pydantic_ai import Agent, UsageLimits, capture_run_messages
from pydantic_ai.exceptions import AgentRunError
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.models.test import TestModel
from pydantic_ai.tool_manager import ToolManager

from ..core.agent import Submit, TurnUsage
from ..core.messages import Message
from . import claude_cli

pydantic_ai.BANNER_ENABLED = False  # no first-run banner in our output

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"  # in the project root
MAX_REQUESTS_PER_TURN = 10  # a normal turn takes 2-3 model requests
TEST_MODEL = "test"  # PydanticAI's free TestModel

Tool = Callable[..., str | Awaitable[str]]
ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]


@dataclass
class Turn:
    """What a tool can see during one agent turn (PydanticAI's ``deps``). Tools never change state
    themselves. They either put messages in ``outbox``, which the handler queues after the turn, or
    ``submit`` a message to the queue to be processed right away and get the replies back."""

    agent: str
    submit: Submit
    outbox: list[Message] = field(default_factory=list)


class AgentTurn(Message):
    """The record of one agent turn, for the log: everything the agent was shown, said and did. No
    agent receives it. What the turn used is logged separately, as a ``TurnUsage`` line."""

    error: str | None = None  # why the turn failed, if it did
    # The turn's new messages, in PydanticAI's format: the prompt (the agent's inbox), the model's
    # text, its tool calls and their results, and the token usage of each request.
    messages: list[ModelMessage] = Field(repr=False)


def turn_usage(model: str, responses: Sequence[ModelResponse]) -> TurnUsage:
    """What a turn's model ``responses`` used, added up."""
    usage = TurnUsage(model=model, requests=len(responses))
    for response in responses:
        usage.input_tokens += response.usage.input_tokens
        usage.output_tokens += response.usage.output_tokens
        usage.reasoning_tokens += response.usage.details.get("reasoning_tokens", 0)
        if (cost := (response.provider_details or {}).get("cost")) is not None:
            usage.cost = (usage.cost or 0.0) + cost
    return usage


class LLMAgent:
    """One LLM participant. It keeps its whole conversation across turns. ``model`` is a name for
    ``make_model`` or a PydanticAI model."""

    def __init__(
        self,
        name: str,
        model: str | Model,
        instructions: str,
        tools: Sequence[Tool],
        reasoning_effort: ReasoningEffort | None = None,
    ) -> None:
        self.name = name
        self.model = make_model(model, reasoning_effort) if isinstance(model, str) else model
        self.agent = Agent(self.model, instructions=instructions, deps_type=Turn, tools=tools)
        self.history: list[ModelMessage] = []

    async def act(self, prompt: str, submit: Submit) -> tuple[list[Message], TurnUsage]:
        """Run one turn, submit a record of it (an ``AgentTurn``), and return the messages the agent
        sent and what the turn used. If the turn fails (for example it makes too many model
        requests), the failure is reported and recorded, and what was sent and used before it
        counts."""
        turn = Turn(agent=self.name, submit=submit)
        error = None
        # Captures the messages even when the run fails, so a failed turn is recorded and its usage
        # counted too.
        with capture_run_messages() as messages:
            try:
                # Run tool calls one at a time, in the order the model made them (sell, then buy).
                with ToolManager.parallel_execution_mode("sequential"):
                    result = await self.agent.run(
                        prompt,
                        deps=turn,
                        message_history=self.history,
                        usage_limits=UsageLimits(request_limit=MAX_REQUESTS_PER_TURN),
                    )
            except AgentRunError as exc:
                error = f"{type(exc).__name__}: {exc}"
                print(f"[{self.name}] turn failed: {error}", file=sys.stderr)
                new = messages[len(self.history) :]  # the history, then this turn's messages
            else:
                new = result.new_messages()
                self.history = result.all_messages()
        await submit(AgentTurn(sender=self.name, error=error, messages=new))
        responses = [m for m in new if isinstance(m, ModelResponse)]
        return turn.outbox, turn_usage(self.model.model_name, responses)


def make_model(name: str, reasoning_effort: ReasoningEffort | None = None) -> Model:
    """``test`` is PydanticAI's free TestModel. ``claude-cli:<model>``, such as ``claude-cli:sonnet``,
    runs a Claude model through ``claude -p`` on a Claude subscription. Anything else is an OpenRouter
    model id, such as ``anthropic/claude-opus-5.5``, using OPENROUTER_API_KEY from the environment or
    the project's .env. OpenRouter reports each response's cost. ``reasoning_effort`` caps
    reasoning; without it the provider's default applies."""
    if name == TEST_MODEL:
        return TestModel()
    if name.startswith(claude_cli.PREFIX):
        return claude_cli.claude_cli_model(name, reasoning_effort)
    load_env(ENV_FILE)
    settings = OpenRouterModelSettings(openrouter_usage={"include": True})
    if reasoning_effort:
        settings["openrouter_reasoning"] = {"effort": reasoning_effort}
    return OpenRouterModel(name, settings=settings)


def load_env(path: Path) -> None:
    """Load KEY=VALUE lines from a .env file into os.environ. Variables that are already set win."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip().removeprefix("export ")
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
