"""What the handler needs from an agent, an LLM or a script: a name, and a way to take a turn."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from .messages import Message

Submit = Callable[[Message], Awaitable[list[Message]]]


@dataclass
class TurnUsage:
    """What one agent turn used, summed over its model requests. ``cost`` is in US dollars, None when
    the provider reported no cost for any of them."""

    model: str
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost: float | None = None


class Agent(Protocol):
    """A participant that takes turns: an LLM (``LLMAgent``) or a script (``ScriptedAgent``). A
    turn sees the agent's inbox as ``prompt``, can ``submit`` messages to be processed right away,
    and returns the messages to queue after it and what its model requests used, None if it used
    no model."""

    name: str

    async def act(self, prompt: str, submit: Submit) -> tuple[list[Message], TurnUsage | None]: ...
