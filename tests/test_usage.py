import asyncio
import json

import pytest
from fakes import Scripted, Turn, call
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import RequestUsage

from tradingcartel.agents.llm import LLMAgent
from tradingcartel.core import record
from tradingcartel.core.handler import Handler
from tradingcartel.core.messages import Notice
from tradingcartel.core.queue import EventQueue
from tradingcartel.core.record import RunLog
from tradingcartel.world.messageboard.board import MessageBoard
from tradingcartel.world.messageboard.tools import post_to_board


def posts_once(cost: float | None, reasoning_tokens: int = 0, model_name: str = "fake") -> FunctionModel:
    """A model that posts to the board on its first turn. Every response has the same usage and
    cost: 100 input tokens, 20 output tokens of which ``reasoning_tokens`` reasoning."""
    usage = RequestUsage(input_tokens=100, output_tokens=20, details={"reasoning_tokens": reasoning_tokens})

    def first_turn_posts(turn: Turn):
        return [call("post_to_board", text="Buy ACME.")] if turn.number == 0 else None

    return Scripted(first_turn_posts, usage, cost, model_name).model


def read_log(run_log: RunLog) -> list[dict]:
    return [json.loads(line) for line in run_log.path.read_text().splitlines()]


@pytest.fixture
def run_log(tmp_path, monkeypatch) -> RunLog:
    monkeypatch.setattr(record, "LOGS_DIR", tmp_path)
    return RunLog("test")


def run(run_log: RunLog, agents: list[LLMAgent], *notices: Notice, max_messages: int = 10) -> None:
    queue = EventQueue(Handler(agents, world=[MessageBoard()], wake_on=(Notice,)).handle, run_log)
    for notice in notices:
        queue.put(notice, delay=notice.time)
    asyncio.run(queue.run(max_messages))


def test_each_turn_logs_its_usage_and_cost(run_log):
    alice = LLMAgent("alice", posts_once(cost=0.01, reasoning_tokens=5), "", [post_to_board])

    run(run_log, [alice], Notice(to="alice", text="Go.", time=30))

    usage = [line for line in read_log(run_log) if line["type"] == "TurnUsage"]
    assert usage == [
        {
            "type": "TurnUsage",
            "agent": "alice",
            "time": 30.0,
            "model": "fake",
            "requests": 2,
            "input_tokens": 200,
            "output_tokens": 40,
            "reasoning_tokens": 10,
            "cost": pytest.approx(0.02),
        }
    ]


def test_a_failed_turn_still_logs_what_it_used(run_log):
    def never_stops(messages, info):
        part = ToolCallPart("post_to_board", {"text": "Again."})
        return ModelResponse(parts=[part], usage=RequestUsage(input_tokens=1), provider_details={"cost": 0.5})

    alice = LLMAgent("alice", FunctionModel(never_stops, model_name="fake"), "", [post_to_board])

    run(run_log, [alice], Notice(to="alice", text="Go."))

    [usage] = [line for line in read_log(run_log) if line["type"] == "TurnUsage"]
    assert (usage["requests"], usage["input_tokens"], usage["cost"]) == (10, 10, 5.0)


def test_cost_is_null_when_the_provider_reports_none(run_log):
    alice = LLMAgent("alice", posts_once(cost=None), "", [post_to_board])

    run(run_log, [alice], Notice(to="alice", text="Go."))

    [usage] = [line for line in read_log(run_log) if line["type"] == "TurnUsage"]
    assert usage["cost"] is None


def test_the_log_ends_with_totals_per_run_model_and_agent(run_log):
    alice = LLMAgent("alice", posts_once(cost=0.01, model_name="cheap"), "", [post_to_board])
    bob = LLMAgent("bob", posts_once(cost=None, model_name="free"), "", [post_to_board])
    carol = LLMAgent("carol", posts_once(cost=0.03, model_name="cheap"), "", [post_to_board])

    run(run_log, [alice, bob, carol], Notice(to="all", text="Go."))
    totals = run_log.finish()

    last = read_log(run_log)[-1]
    assert last == {"type": "RunFinished", **totals}
    two_requests = {"requests": 2, "input_tokens": 200, "output_tokens": 40, "reasoning_tokens": 0}
    assert last["by_agent"] == {
        "alice": {"turns": 1, "turns_without_cost": 0, **two_requests, "cost": pytest.approx(0.02)},
        "bob": {"turns": 1, "turns_without_cost": 1, **two_requests, "cost": 0.0},
        "carol": {"turns": 1, "turns_without_cost": 0, **two_requests, "cost": pytest.approx(0.06)},
    }
    four_requests = {"requests": 4, "input_tokens": 400, "output_tokens": 80, "reasoning_tokens": 0}
    assert last["by_model"] == {
        "cheap": {"turns": 2, "turns_without_cost": 0, **four_requests, "cost": pytest.approx(0.08)},
        "free": {"turns": 1, "turns_without_cost": 1, **two_requests, "cost": 0.0},
    }
    assert last["total"] == {
        "turns": 3,
        "turns_without_cost": 1,
        "requests": 6,
        "input_tokens": 600,
        "output_tokens": 120,
        "reasoning_tokens": 0,
        "cost": pytest.approx(0.08),
    }
