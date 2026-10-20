"""The event queue: the one queue that every message in a simulation goes through.

Every message is scheduled at a simulated time, and the queue always processes the earliest one next
(ties in the order they were put). The clock, ``now``, counts simulated minutes since the start. It
never reads the computer's clock: it jumps to each message's time as that message is processed.
"""

import heapq
import itertools
import math
from collections.abc import Awaitable, Callable

from .messages import Message

Handler = Callable[[Message], Awaitable[list[Message]]]


class EventQueue:
    """The handler returns the messages that follow from each message; they happen now. Every
    processed message is kept in ``log``."""

    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self.now = 0.0  # simulated minutes since the start
        self.log: list[Message] = []
        self._heap: list[tuple[float, int, Message]] = []
        self._order = itertools.count()  # breaks ties between messages at the same time

    def put(self, message: Message, delay: float = 0.0) -> None:
        """Schedule a message ``delay`` simulated minutes from now."""
        message = message.model_copy(update={"time": self.now + delay})
        heapq.heappush(self._heap, (message.time, next(self._order), message))

    async def run(self, max_messages: int, until: float = math.inf) -> None:
        """Process messages in time order until none are left up to ``until`` (simulated minutes),
        or ``max_messages`` have been processed in total (a cost brake)."""
        while self._heap and self._heap[0][0] <= until and len(self.log) < max_messages:
            self.now, _, message = heapq.heappop(self._heap)
            self.log.append(message)
            for new in await self.handler(message):
                self.put(new)
