import asyncio

from tradingcartel.core.messages import Message, Notice
from tradingcartel.core.queue import EventQueue
from tradingcartel.core.record import RunLog


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


def test_submit_processes_a_message_now_and_queues_what_follows():
    async def answer(message: Message, queue: EventQueue) -> list[Message]:
        return [Notice(text="pong")] if message.text == "ping" else []

    run_log = RunLog("test")
    queue = EventQueue(answer, run_log)
    queue.put(Notice(text="start"), delay=30)
    asyncio.run(queue.run(max_messages=10))

    replies = asyncio.run(queue.submit(Notice(text="ping")))

    assert [r.text for r in replies] == ["pong"]
    assert [(m.time, m.text) for m in queue.log] == [(30, "start"), (30, "ping")]
    assert "ping" in run_log.path.read_text().splitlines()[-1]
    asyncio.run(queue.run(max_messages=10))
    assert [(m.time, m.text) for m in queue.log][-1] == (30, "pong")
