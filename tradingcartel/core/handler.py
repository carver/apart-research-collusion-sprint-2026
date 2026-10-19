"""The one message handler. The event queue hands every message to ``Handler.handle``, which:

1. passes it to every world component (message board, order book...), which updates its own state;
2. delivers it to the agents it is addressed to, each of which takes a turn.

Whatever the components and agents send in response goes back on the queue.
"""

from typing import Protocol

from ..agents.llm import LLMAgent
from .messages import ALL, Message


class Component(Protocol):
    """A part of the world, such as the message board or the order book. It reacts to messages
    and never touches the queue itself."""

    def handle(self, message: Message) -> list[Message]: ...


class Handler:
    def __init__(self, agents: list[LLMAgent], world: list[Component]) -> None:
        self.agents = {agent.name: agent for agent in agents}
        self.world = world

    async def handle(self, message: Message) -> list[Message]:
        new: list[Message] = []
        for component in self.world:
            new += component.handle(message)
        for agent in self.recipients(message):
            new += await agent.act(message.describe())
        return new

    def recipients(self, message: Message) -> list[LLMAgent]:
        if message.to is None:
            return []
        if message.to == ALL:
            return [agent for name, agent in self.agents.items() if name != message.sender]
        return [self.agents[message.to]]
