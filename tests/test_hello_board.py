import asyncio

from tradingcartel.experiments.hello_board.run import Settings, run
from tradingcartel.world.messageboard.board import BoardPost


def test_hello_board_runs_for_free():
    queue = asyncio.run(run(Settings(max_messages=20)))

    # TestModel calls tools only in the first request of a conversation, and agents keep their
    # conversation, so each agent posts once: on its first turn.
    assert [m.sender for m in queue.log if isinstance(m, BoardPost)] == ["alice", "bob", "carol"]


def test_main_runs_the_experiment_then_finishes_the_log(monkeypatch, capsys):
    import json
    import sys
    from pathlib import Path

    from tradingcartel.experiments.hello_board.run import main

    monkeypatch.setattr(sys, "argv", ["run", "--write", "--max-messages", "20"])

    main()

    printed = capsys.readouterr().out
    path = printed.rsplit("Log: ", 1)[1].strip()
    logged = [json.loads(line)["type"] for line in Path(path).read_text().splitlines()]
    assert logged[0] == "RunStarted" and logged[-1] == "RunFinished"
    assert "BoardPost" in printed  # the experiment's own report
    assert "total: " in printed
