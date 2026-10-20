"""Fake models that script what agents do, for tests that need real moves."""

import re
from collections.abc import Callable
from dataclasses import dataclass

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import RequestUsage

from tradingcartel.core.messages import Message


@dataclass(frozen=True)
class Turn:
    """An agent's turn: ``agent`` is its name (None when its instructions don't start "You are
    NAME,"), ``prompt`` what it was shown, and ``number`` how many turns it took before this one."""

    agent: str | None
    prompt: str
    number: int


def call(tool: str, **args) -> ToolCallPart:
    return ToolCallPart(tool, args)


class Scripted:
    """A fake model that any number of agents can share. On each turn, ``script(turn)`` gives the
    agent's tool calls (none: it does nothing); once their results come back, the agent says it's
    done. Every response reports ``usage``, and ``cost`` if given. ``prompts[agent]`` holds what each
    agent was shown, turn by turn; ``instructions[agent]`` and ``tools[agent]`` its instructions and
    the names of its tools."""

    def __init__(
        self,
        script: Callable[[Turn], list[ToolCallPart] | None],
        usage: RequestUsage | None = None,
        cost: float | None = None,
        model_name: str = "fake",
    ) -> None:
        self.script = script
        self.usage = usage or RequestUsage()
        self.cost = cost
        self.prompts: dict[str | None, list[str]] = {}
        self.instructions: dict[str | None, str] = {}
        self.tools: dict[str | None, list[str]] = {}
        self.model = FunctionModel(self.respond, model_name=model_name)

    def respond(self, messages, info) -> ModelResponse:
        latest = messages[-1].parts
        if any(isinstance(part, ToolReturnPart) for part in latest):
            parts = [TextPart("done")]
        else:
            named = re.match(r"You are (\w+),", info.instructions or "")
            agent = named.group(1) if named else None
            prompt = "\n".join(str(part.content) for part in latest if isinstance(part, UserPromptPart))
            self.instructions[agent] = info.instructions or ""
            self.tools[agent] = [tool.name for tool in info.function_tools]
            turns = self.prompts.setdefault(agent, [])
            turns.append(prompt)
            parts = self.script(Turn(agent, prompt, len(turns) - 1)) or [TextPart("nothing to do")]
        details = {} if self.cost is None else {"cost": self.cost}
        return ModelResponse(parts=parts, usage=self.usage, provider_details=details)


async def no_submit(message: Message) -> list[Message]:
    """A ``submit`` for agents that must not submit anything."""
    raise AssertionError(f"submitted {message!r}")
