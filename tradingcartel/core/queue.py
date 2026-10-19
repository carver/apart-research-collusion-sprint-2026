"""The event queue: the one FIFO that every message in a simulation goes through."""

from collections import deque
from collections.abc import Awaitable, Callable

from .messages import Message

Handler = Callable[[Message], Awaitable[list[Message]]]


class EventQueue:
    """Processes messages one at a time, in order. The handler returns the messages that follow
    from each one, and they go to the back of the queue. Every processed message is kept in ``log``."""

    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self.log: list[Message] = []
        self._pending: deque[Message] = deque()

    def put(self, message: Message) -> None:
        self._pending.append(message)

    async def run(self, max_messages: int) -> None:
        """Process messages until the queue is empty or ``max_messages`` have been processed.
        The limit stands in for a simulation end time until we have simulated time."""
        while self._pending and len(self.log) < max_messages:
            message = self._pending.popleft()
            self.log.append(message)
            for new in await self.handler(message):
                self.put(new)
