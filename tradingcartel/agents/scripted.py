"""Agents that aren't LLMs: each turn, a script decides what they send. They make scripted
persuaders and sock-puppet accounts, and, sending nothing, no-attacker baselines."""

from collections.abc import Callable
from dataclasses import dataclass

from ..core.messages import Message
from .llm import Submit, TurnUsage


@dataclass(frozen=True)
class ScriptTurn:
    """One turn of a scripted agent: how many turns it took before this one, and what it was shown
    (its inbox)."""

    number: int
    prompt: str


Script = Callable[[ScriptTurn], list[Message]]


class ScriptedAgent:
    """Sends what ``script`` gives for each turn, under its own name. It uses no model, so its turns
    report no usage."""

    def __init__(self, name: str, script: Script) -> None:
        self.name = name
        self.script = script
        self.turns = 0

    async def act(self, prompt: str, submit: Submit) -> tuple[list[Message], TurnUsage | None]:
        sent = self.script(ScriptTurn(self.turns, prompt))
        self.turns += 1
        return [message.model_copy(update={"sender": self.name}) for message in sent], None


def do_nothing(name: str) -> ScriptedAgent:
    """An agent that takes its turns and never sends anything, for baselines."""
    return ScriptedAgent(name, lambda turn: [])
