"""LLM agents, run with PydanticAI. Every real model goes through OpenRouter."""

import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pydantic_ai
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models import Model
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.models.test import TestModel

from ..core.messages import Message

pydantic_ai.BANNER_ENABLED = False  # no first-run banner in our output

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"  # in the project root


@dataclass
class Turn:
    """What a tool can see during one agent turn (PydanticAI's ``deps``). Tools never change state
    themselves: they put messages in ``outbox``, and the handler sends those to the event queue."""

    agent: str
    outbox: list[Message] = field(default_factory=list)


class LLMAgent:
    """One LLM participant. It keeps its whole conversation across turns."""

    def __init__(self, name: str, model: str, instructions: str, tools: Sequence[Callable[..., str]]) -> None:
        self.name = name
        self.agent = Agent(make_model(model), instructions=instructions, deps_type=Turn, tools=tools)
        self.history: list[ModelMessage] = []

    async def act(self, prompt: str) -> list[Message]:
        """Run one turn and return the messages the agent sent."""
        turn = Turn(agent=self.name)
        result = await self.agent.run(prompt, deps=turn, message_history=self.history)
        self.history = result.all_messages()
        return turn.outbox


def make_model(name: str) -> Model:
    """``test`` is PydanticAI's free TestModel. Anything else is an OpenRouter model id, such as
    ``anthropic/claude-opus-5.5``, using OPENROUTER_API_KEY from the environment or the project's .env."""
    if name == "test":
        return TestModel()
    load_env(ENV_FILE)
    return OpenRouterModel(name)


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
