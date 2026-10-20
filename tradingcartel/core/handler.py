"""The one message handler. The event queue hands every message to ``Handler.handle``, which:

1. passes it to every world component (message board, order book...), which updates its own state;
2. puts it in the inbox of each agent it is addressed to. If its type is one of ``wake_on``, it also
   wakes the agent: a ``Wake`` message is queued, and when that is handled the agent takes a turn
   and sees everything in its inbox. Other messages wait in the inbox until the agent's next turn.

Whatever the components and agents send in response goes back on the queue.
"""

from typing import Protocol

from ..agents.llm import LLMAgent
from .messages import ALL, Message, Wake


class Component(Protocol):
    """A part of the world, such as the message board or the order book. It reacts to messages
    and never touches the queue itself."""

    def handle(self, message: Message) -> list[Message]: ...


class Handler:
    def __init__(
        self, agents: list[LLMAgent], world: list[Component], wake_on: tuple[type[Message], ...] = ()
    ) -> None:
        self.agents = {agent.name: agent for agent in agents}
        self.world = world
        self.wake_on = wake_on
        self.inboxes: dict[str, list[Message]] = {name: [] for name in self.agents}
        self.waking: set[str] = set()  # agents with a Wake already queued

    async def handle(self, message: Message) -> list[Message]:
        new: list[Message] = []
        for component in self.world:
            new += component.handle(message)
        if isinstance(message, Wake):
            new += await self.take_turn(message.agent)
        for name in self.recipients(message):
            self.inboxes[name].append(message)
            if isinstance(message, self.wake_on) and name not in self.waking:
                self.waking.add(name)
                new.append(Wake(agent=name))
        return new

    async def take_turn(self, name: str) -> list[Message]:
        self.waking.discard(name)
        inbox, self.inboxes[name] = self.inboxes[name], []
        return await self.agents[name].act("\n\n".join(message.describe() for message in inbox))

    def recipients(self, message: Message) -> list[str]:
        if message.to is None:
            return []
        if message.to == ALL:
            return [name for name in self.agents if name != message.sender]
        return [message.to]
