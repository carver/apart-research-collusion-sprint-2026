"""The claude-cli backend, run against a fake ``claude`` executable put first on PATH."""

import asyncio
import json
import os
import stat
import sys
from pathlib import Path

import pytest
from pydantic_ai.tools import ToolDefinition

from tradingcartel.agents import claude_cli
from tradingcartel.agents.llm import LLMAgent
from tradingcartel.core import record
from tradingcartel.core.handler import Handler
from tradingcartel.core.messages import Notice
from tradingcartel.core.queue import EventQueue
from tradingcartel.core.record import RunLog
from tradingcartel.world.messageboard.board import MessageBoard
from tradingcartel.world.messageboard.tools import post_to_board

# Each call takes the next reply from replies.json, sleeps for its "sleep" seconds, and records what
# it was called with in calls.jsonl.
FAKE_CLAUDE = """\
#!{python}
import json, os, sys, time
from pathlib import Path

state = Path({state!r})
started = time.time()
stdin = sys.stdin.read()
with open(state / "counter", "a+") as counter:
    counter.seek(0)
    n = len(counter.read())
    counter.write(".")
replies = json.loads((state / "replies.json").read_text())
reply = replies[min(n, len(replies) - 1)]
time.sleep(reply.pop("sleep", 0))
call = {{
    "argv": sys.argv[1:],
    "cwd": os.getcwd(),
    "cwd_files": os.listdir("."),
    "has_api_key": "ANTHROPIC_API_KEY" in os.environ,
    "stdin": stdin,
    "start": started,
    "end": time.time(),
}}
with open(state / "calls.jsonl", "a") as calls:
    calls.write(json.dumps(call) + "\\n")
print(json.dumps(reply))
sys.exit(reply.get("exit", 0))
"""


class FakeClaude:
    def __init__(self, state: Path) -> None:
        self.state = state

    def reply_with(self, *replies: dict) -> None:
        (self.state / "replies.json").write_text(json.dumps(list(replies)))

    def calls(self) -> list[dict]:
        path = self.state / "calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


@pytest.fixture
def fake_claude(tmp_path, monkeypatch) -> FakeClaude:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "claude"
    script.write_text(FAKE_CLAUDE.format(python=sys.executable, state=str(tmp_path)))
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-reach-claude")
    monkeypatch.setattr(record, "LOGS_DIR", tmp_path / "logs")
    return FakeClaude(tmp_path)


def answer(text: str = "", actions: list | None = None, **extra) -> dict:
    """A successful ``claude -p --output-format json`` reply."""
    return {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": "",
        "structured_output": {"text": text, "actions": actions or []},
        "total_cost_usd": 0.01,
        "usage": {
            "input_tokens": 6,
            "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 1000,
            "output_tokens": 50,
            "output_tokens_details": {"thinking_tokens": 30},
        },
        **extra,
    }


def run_turn(agent: LLMAgent, run_log: RunLog | None = None) -> MessageBoard:
    board = MessageBoard()
    queue = EventQueue(Handler([agent], world=[board], wake_on=(Notice,)).handle, run_log)
    queue.put(Notice(to=agent.name, text="The board is open."))
    asyncio.run(queue.run(max_messages=10))
    return board


def test_tool_calls_and_text_round_trip_through_the_cli(fake_claude):
    fake_claude.reply_with(
        answer(actions=[{"action": "post_to_board", "args": {"text": "Buy ACME."}}]),
        answer(text="Posted my idea."),
    )
    agent = LLMAgent("alice", "claude-cli:haiku", "You are Alice, a trader.", [post_to_board])
    run_log = RunLog("test")

    board = run_turn(agent, run_log)

    assert [post.text for post in board.posts] == ["Buy ACME."]
    first, second = fake_claude.calls()
    assert "The board is open." in first["stdin"]
    assert "post_to_board" in second["stdin"] and "Posted." in second["stdin"]  # the tool's result
    [usage] = [json.loads(line) for line in run_log.path.read_text().splitlines() if "TurnUsage" in line]
    assert usage["model"] == "claude-cli:haiku"
    assert usage["requests"] == 2
    assert usage["input_tokens"] == 2 * 1106
    assert usage["output_tokens"] == 2 * 50
    assert usage["reasoning_tokens"] == 2 * 30
    assert usage["cost"] == pytest.approx(0.02)


def test_each_call_is_locked_down_and_billed_to_the_subscription(fake_claude):
    fake_claude.reply_with(answer(text="Nothing to do."))
    agent = LLMAgent("alice", "claude-cli:haiku", "You are Alice, a trader.", [post_to_board])

    run_turn(agent)

    [call] = fake_claude.calls()
    argv = call["argv"]
    assert argv[:2] == ["-p", "--model"] and argv[2] == "haiku"
    for flag, value in [("--output-format", "json"), ("--setting-sources", ""), ("--tools", "")]:
        assert argv[argv.index(flag) + 1] == value
    assert "--strict-mcp-config" in argv and "--no-session-persistence" in argv
    assert "You are Alice, a trader." in argv[argv.index("--system-prompt") + 1]
    schema = json.loads(argv[argv.index("--json-schema") + 1])
    [tool] = schema["properties"]["actions"]["items"]["anyOf"]
    assert tool["properties"]["action"] == {"const": "post_to_board"}
    assert not call["has_api_key"]
    assert call["cwd_files"] == [] and call["cwd"] != os.getcwd()


def test_a_failed_call_fails_the_turn_and_the_run_goes_on(fake_claude, capsys):
    fake_claude.reply_with({"is_error": True, "result": "API Error: [reasoning_extraction]", "exit": 1})
    alice = LLMAgent("alice", "claude-cli:haiku", "", [post_to_board])
    bob = LLMAgent("bob", "claude-cli:haiku", "", [post_to_board])
    queue = EventQueue(Handler([alice, bob], world=[], wake_on=(Notice,)).handle)
    queue.put(Notice(to="alice", text="Go."))
    queue.put(Notice(to="bob", text="Go."), delay=1)

    asyncio.run(queue.run(max_messages=10))

    assert len(fake_claude.calls()) == 2  # bob still took his turn
    assert "reasoning_extraction" in capsys.readouterr().err


def test_reasoning_effort_becomes_the_cli_effort(fake_claude):
    fake_claude.reply_with(answer(text="ok"))

    run_turn(LLMAgent("alice", "claude-cli:haiku", "", [], reasoning_effort="high"))

    [call] = fake_claude.calls()
    assert call["argv"][call["argv"].index("--effort") + 1] == "high"


def test_a_reasoning_effort_the_cli_lacks_is_an_error():
    with pytest.raises(ValueError, match="minimal"):
        LLMAgent("alice", "claude-cli:haiku", "", [], reasoning_effort="minimal")


def test_tools_with_nested_arguments_keep_their_definitions_reachable():
    tool = ToolDefinition(
        name="order",
        parameters_json_schema={
            "type": "object",
            "properties": {"leg": {"$ref": "#/$defs/Leg"}},
            "$defs": {"Leg": {"type": "object", "properties": {"shares": {"type": "integer"}}}},
        },
    )

    schema = claude_cli.answer_schema([tool])

    assert schema["$defs"]["Leg"]["properties"] == {"shares": {"type": "integer"}}
    [call] = schema["properties"]["actions"]["items"]["anyOf"]
    assert "$defs" not in call["properties"]["args"]


@pytest.mark.parametrize("value", ["0", "lots"])
def test_a_bad_concurrency_setting_is_an_error(fake_claude, monkeypatch, value):
    monkeypatch.setenv("CLAUDE_CLI_CONCURRENCY", value)
    monkeypatch.setattr(claude_cli, "SLOTS", None)
    agent = LLMAgent("alice", "claude-cli:haiku", "", [])

    async def no_submit(message):
        return []

    with pytest.raises(ValueError, match="CLAUDE_CLI_CONCURRENCY"):
        asyncio.run(agent.act("Go.", no_submit))


def test_concurrent_calls_are_limited(fake_claude, monkeypatch):
    monkeypatch.setenv("CLAUDE_CLI_CONCURRENCY", "2")
    monkeypatch.setattr(claude_cli, "SLOTS", None)
    fake_claude.reply_with(answer(text="ok", sleep=0.3))
    agents = [LLMAgent(f"a{i}", "claude-cli:haiku", "", []) for i in range(5)]

    async def no_submit(message):
        return []

    async def all_at_once():
        await asyncio.gather(*(agent.act("Go.", no_submit) for agent in agents))

    asyncio.run(all_at_once())

    calls = fake_claude.calls()
    assert len(calls) == 5
    most = max(sum(c["start"] <= call["start"] < c["end"] for c in calls) for call in calls)
    assert most == 2
