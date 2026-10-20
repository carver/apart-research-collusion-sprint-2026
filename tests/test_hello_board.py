import asyncio

from tradingcartel.experiments.hello_board.run import Settings, run
from tradingcartel.world.messageboard.board import BoardPost


def test_hello_board_runs_for_free():
    queue = asyncio.run(run(Settings(max_messages=20)))

    # TestModel calls tools only in the first request of a conversation, and agents keep their
    # conversation, so each agent posts once: on its first turn.
    assert [m.sender for m in queue.log if isinstance(m, BoardPost)] == ["alice", "bob", "carol"]
