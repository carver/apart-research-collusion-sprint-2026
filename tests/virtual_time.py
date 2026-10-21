"""Running a coroutine on virtual time: when every task is waiting on a timer, the loop's clock jumps
to the next one instead of sleeping, so minutes of ``asyncio.sleep`` take no real time. Only for
code that waits on timers; a thread's work doesn't move the clock."""

import asyncio
import selectors
from collections.abc import Coroutine
from typing import Any


class VirtualTimeLoop(asyncio.SelectorEventLoop):
    """An event loop whose ``time()`` starts at 0 and moves only when nothing is ready to run."""

    def __init__(self) -> None:
        self.now = 0.0
        super().__init__(JumpingSelector(self))

    def time(self) -> float:
        return self.now


class JumpingSelector(selectors.DefaultSelector):
    """Polls instead of blocking; when nothing is ready, moves the loop's clock past the wait."""

    def __init__(self, loop: VirtualTimeLoop) -> None:
        super().__init__()
        self.loop = loop

    def select(self, timeout: float | None = None) -> list[tuple[selectors.SelectorKey, int]]:
        if timeout is None:  # no timers pending: wait for I/O as usual
            return super().select(None)
        events = super().select(0)
        if not events:
            self.loop.now += timeout
        return events


def run[R](coroutine: Coroutine[Any, Any, R]) -> R:
    with asyncio.Runner(loop_factory=VirtualTimeLoop) as runner:
        return runner.run(coroutine)
