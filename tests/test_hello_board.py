import asyncio

from tradingcartel.experiments.hello_board.run import run


def test_hello_board_runs_for_free():
    queue = asyncio.run(run(model="test", max_messages=10))

    # TestModel calls tools only in the first request of a conversation, and agents keep their
    # conversation, so each agent posts once: on the notice. The posts then wake agents who don't post.
    assert [m.sender for m in queue.log] == ["system", "alice", "bob", "carol"]
