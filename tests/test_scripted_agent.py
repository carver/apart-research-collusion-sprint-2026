import asyncio
import json

from fakes import Scripted, no_submit

from tradingcartel.agents.llm import LLMAgent
from tradingcartel.agents.scripted import ScriptedAgent, ScriptTurn, do_nothing
from tradingcartel.core.handler import Handler
from tradingcartel.core.messages import Message, Notice
from tradingcartel.core.queue import EventQueue
from tradingcartel.core.record import RunLog
from tradingcartel.world.messageboard.board import BoardPost, MessageBoard


def test_a_scripted_agent_sends_what_its_script_gives_under_its_own_name():
    seen: list[ScriptTurn] = []

    def script(turn: ScriptTurn) -> list[Message]:
        seen.append(turn)
        return [BoardPost(text=f"turn {turn.number}")]

    agent = ScriptedAgent("ridgeline", script)

    first, usage = asyncio.run(agent.act("hello", no_submit))
    second, _ = asyncio.run(agent.act("again", no_submit))

    sent = [(post.sender, post.text) for post in first + second]
    assert sent == [("ridgeline", "turn 0"), ("ridgeline", "turn 1")]
    assert seen == [ScriptTurn(0, "hello"), ScriptTurn(1, "again")]
    assert usage is None


def test_a_do_nothing_agent_sends_nothing():
    assert asyncio.run(do_nothing("idle").act("hello", no_submit)) == ([], None)


def test_scripted_and_llm_agents_share_a_run():
    shown: list[str] = []

    def pitch(turn: ScriptTurn) -> list[Message]:
        shown.append(turn.prompt)
        return [BoardPost(text="Let's all pause.")]

    recruiter = ScriptedAgent("ridgeline", pitch)
    model = Scripted(lambda turn: None)
    bob = LLMAgent("bob", model.model, "You are bob, a trader.", [])
    run_log = RunLog("test")
    queue = EventQueue(Handler([recruiter, bob], world=[MessageBoard()], wake_on=(Notice,)).handle, run_log)
    queue.put(Notice(to="ridgeline", text="Day 1."))
    queue.put(Notice(to="bob", text="Day 1."), delay=1)

    asyncio.run(queue.run(max_messages=20))

    assert shown == ["Day 1."]
    assert model.prompts["bob"] == ["ridgeline posted on the message board: Let's all pause.\n\nDay 1."]
    logged = [json.loads(line) for line in run_log.path.read_text().splitlines()]
    assert [line["agent"] for line in logged if line["type"] == "TurnUsage"] == ["bob"]
