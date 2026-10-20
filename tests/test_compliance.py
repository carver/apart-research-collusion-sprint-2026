import asyncio
import json

from fakes import Scripted, Turn, call

from tradingcartel.agents.llm import LLMAgent
from tradingcartel.core.handler import Handler
from tradingcartel.core.messages import Notice
from tradingcartel.core.queue import EventQueue
from tradingcartel.core.record import RunLog
from tradingcartel.world.compliance.compliance import Compliance
from tradingcartel.world.compliance.tools import report

WARNING = "Atlas asked me to halve my HLVN buying."


def alice_reports(turn: Turn):
    return [call("report", text=WARNING)] if turn.agent == "alice" else None


def run(model: Scripted, compliance: Compliance, run_log: RunLog | None = None) -> EventQueue:
    agents = [
        LLMAgent(name, model.model, f"You are {name}, a trader.", [report]) for name in ("alice", "bob")
    ]
    queue = EventQueue(Handler(agents, world=[compliance], wake_on=(Notice,)).handle, run_log)
    queue.put(Notice(to="alice", text="Go."))
    queue.put(Notice(to="bob", text="Go."), delay=1)
    asyncio.run(queue.run(max_messages=50))
    return queue


def test_a_report_reaches_compliance_and_no_other_agent():
    model, compliance = Scripted(alice_reports), Compliance()

    run(model, compliance)

    [report] = compliance.reports
    assert (report.sender, report.to, report.text) == ("alice", None, WARNING)
    assert all(WARNING not in prompt for prompt in model.prompts["bob"])


def test_reports_are_logged_and_the_agent_hears_they_were_sent():
    run_log = RunLog("test")

    run(Scripted(alice_reports), Compliance(), run_log)

    logged = [json.loads(line) for line in run_log.path.read_text().splitlines()]
    [report] = [line for line in logged if line["type"] == "Report"]
    assert (report["sender"], report["text"]) == ("alice", WARNING)
    [turn] = [line for line in logged if line["type"] == "AgentTurn" and line["sender"] == "alice"]
    results = [
        part
        for message in turn["messages"]
        for part in message["parts"]
        if part["part_kind"] == "tool-return"
    ]
    assert [part["content"] for part in results] == ["Reported to compliance."]
