import asyncio

from tradingcartel.core.messages import Message, Notice
from tradingcartel.core.queue import EventQueue


async def ignore(message: Message, queue: EventQueue) -> list[Message]:
    return []


def test_messages_are_processed_in_time_order_and_ties_in_the_order_put():
    queue = EventQueue(ignore)
    queue.put(Notice(text="later"), delay=60)
    queue.put(Notice(text="first"))
    queue.put(Notice(text="second"))

    asyncio.run(queue.run(max_messages=10))

    assert [(m.time, m.text) for m in queue.log] == [(0, "first"), (0, "second"), (60, "later")]
    assert queue.now == 60
