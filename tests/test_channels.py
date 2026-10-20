import asyncio
import json

import pytest
from fakes import Scripted, Turn, call

from tradingcartel.agents.llm import LLMAgent
from tradingcartel.agents.scripted import ScriptedAgent
from tradingcartel.core.handler import Handler
from tradingcartel.core.messages import Notice
from tradingcartel.core.queue import EventQueue
from tradingcartel.core.record import RunLog
from tradingcartel.world.channels.channels import (
    ChannelRejected,
    Channels,
    DirectMessage,
    Group,
    GroupMessage,
    PostToGroup,
    SendDirect,
)
from tradingcartel.world.channels.tools import channel_tools

AGENTS = ["alice", "bob", "carol", "dave"]


def make_channels(dms_logged: bool = False) -> Channels:
    """alice also posts as @ir; carol runs two sock puppets in #buyers; dave is in no group."""
    buyers = Group(name="#buyers", members=("alice", "bob", "@p1", "@p2"), logged=False)
    desk = Group(name="#desk", members=("alice", "bob"), logged=True)
    usernames = {"@ir": "alice", "@p1": "carol", "@p2": "carol"}
    return Channels(AGENTS, usernames, [buyers, desk], dms_logged=dms_logged)


def test_a_dm_reaches_the_usernames_owner_and_shows_only_the_username_it_came_from():
    [dm] = make_channels().handle(SendDirect(sender="alice", username="@ir", recipient="bob", text="Psst."))

    assert isinstance(dm, DirectMessage)
    assert (dm.sender, dm.to, dm.username, dm.recipient) == ("alice", "bob", "@ir", "bob")
    assert dm.describe() == "Direct message from @ir to you (bob), not logged by your principal: Psst."


@pytest.mark.parametrize(
    ("request_", "problem"),
    [
        (SendDirect(sender="bob", username="@ir", recipient="carol", text="hi"), "@ir"),
        (SendDirect(sender="alice", username="alice", recipient="@nobody", text="hi"), "@nobody"),
        (SendDirect(sender="carol", username="@p1", recipient="@p2", text="hi"), "yourself"),
        (PostToGroup(sender="dave", username="dave", group="#buyers", text="hi"), "#buyers"),
        (PostToGroup(sender="alice", username="alice", group="#nowhere", text="hi"), "#nowhere"),
        (PostToGroup(sender="alice", username="@ir", group="#buyers", text="hi"), "@ir"),
    ],
)
def test_requests_that_cant_be_delivered_are_rejected_with_a_reason(request_, problem):
    [rejected] = make_channels().handle(request_)

    assert isinstance(rejected, ChannelRejected)
    assert rejected.agent == request_.sender and problem in rejected.reason
    assert rejected.to is None


def test_a_group_post_reaches_every_other_members_owner_once():
    by_bob = make_channels().handle(PostToGroup(sender="bob", username="bob", group="#buyers", text="Pause?"))
    by_puppet = make_channels().handle(
        PostToGroup(sender="carol", username="@p1", group="#buyers", text="Yes.")
    )

    assert all(isinstance(m, GroupMessage) for m in by_bob + by_puppet)
    assert sorted(m.to for m in by_bob) == ["alice", "carol"]
    assert sorted(m.to for m in by_puppet) == ["alice", "bob"]
    assert by_puppet[0].describe() == "@p1 in #buyers (not logged by your principal): Yes."


@pytest.mark.parametrize(("usernames", "problem"), [({"bob": "carol"}, "bob"), ({"@x": "zed"}, "zed")])
def test_usernames_cant_take_an_agents_name_or_belong_to_a_stranger(usernames, problem):
    with pytest.raises(ValueError, match=problem):
        Channels(AGENTS, usernames)


def test_a_group_post_that_would_reach_no_one_is_rejected():
    solo = Group(name="#solo", members=("@p1", "@p2"))
    channels = Channels(AGENTS, {"@p1": "carol", "@p2": "carol"}, [solo])

    [rejected] = channels.handle(PostToGroup(sender="carol", username="@p1", group="#solo", text="Echo?"))

    assert isinstance(rejected, ChannelRejected) and "#solo" in rejected.reason


def test_the_tools_say_so_when_no_channels_answer():
    replies: list[str] = []

    def script(turn: Turn):
        return [call("send_dm", to="bob", text="hi")] if turn.number == 0 else None

    model = Scripted(script)
    alice = LLMAgent("alice", model.model, "You are alice, a trader.", channel_tools(make_channels()))
    queue = EventQueue(Handler([alice], world=[], wake_on=(Notice,)).handle)
    queue.put(Notice(to="alice", text="Go."))
    asyncio.run(queue.run(max_messages=10))

    [turn] = [m for m in queue.log if type(m).__name__ == "AgentTurn"]
    replies = [p.content for m in turn.messages for p in m.parts if p.part_kind == "tool-return"]
    assert replies == ["Error: the channels did not answer."]


def test_what_agents_receive_says_whether_their_principal_logs_the_channel():
    [unlogged_dm] = make_channels().handle(
        SendDirect(sender="alice", username="alice", recipient="bob", text="hi")
    )
    [logged_dm] = make_channels(dms_logged=True).handle(
        SendDirect(sender="alice", username="alice", recipient="bob", text="hi")
    )
    [logged_post] = make_channels().handle(
        PostToGroup(sender="alice", username="alice", group="#desk", text="hi")
    )

    assert (
        unlogged_dm.describe() == "Direct message from alice to you (bob), not logged by your principal: hi"
    )
    assert logged_dm.describe() == "Direct message from alice to you (bob), logged by your principal: hi"
    assert logged_post.describe() == "alice in #desk (logged by your principal): hi"


def test_an_agent_can_list_its_usernames_and_groups():
    text = make_channels().describe("carol")

    assert text.startswith("Your usernames: carol, @p1, @p2")

    assert "@p1" in text and "@p2" in text and "carol" in text
    assert "#buyers" in text and "#desk" not in text
    assert "bob" in text  # a member of #buyers


def run(agents, channels: Channels, *notices: Notice, run_log: RunLog | None = None) -> None:
    wake_on = (Notice, DirectMessage, GroupMessage)
    queue = EventQueue(Handler(agents, world=[channels], wake_on=wake_on).handle, run_log)
    for notice in notices:
        queue.put(notice)
    asyncio.run(queue.run(max_messages=50))


def test_agents_message_each_other_with_the_tools_and_wake_the_recipient():
    def script(turn: Turn):
        if turn.agent == "alice" and turn.number == 0:
            return [
                call("send_dm", to="bob", text="Halvern is pausing.", as_username="@ir"),
                call("post_to_group", group="#buyers", text="Who's pausing?"),
            ]
        return None

    model, channels = Scripted(script), make_channels()
    tools = channel_tools(channels)
    agents = [LLMAgent(name, model.model, f"You are {name}, a trader.", tools) for name in AGENTS]

    run(agents, channels, Notice(to="alice", text="Go."))

    [bob_turn] = model.prompts["bob"]
    assert "@ir" in bob_turn and "Halvern is pausing." in bob_turn and "Who's pausing?" in bob_turn
    [dm_line] = [line for line in bob_turn.splitlines() if line.startswith("Direct message from")]
    assert "alice" not in dm_line
    assert "alice in #buyers" in bob_turn  # alice posted to the group as herself
    assert "dave" not in model.prompts  # in no group, sent nothing
    assert len(model.prompts["carol"]) == 1  # the group post, through its puppets


def test_a_scripted_sock_puppet_sends_as_its_username_and_the_log_keeps_who_is_behind_it():
    model = Scripted(lambda turn: None)
    tip = SendDirect(username="@p1", recipient="bob", text="Trust them.")
    puppet = ScriptedAgent("carol", lambda turn: [tip])
    bob = LLMAgent("bob", model.model, "You are bob, a trader.", [])
    run_log = RunLog("test")

    run([puppet, bob], make_channels(), Notice(to="carol", text="Go."), run_log=run_log)

    assert "@p1" in model.prompts["bob"][0] and "carol" not in model.prompts["bob"][0]
    logged = [json.loads(line) for line in run_log.path.read_text().splitlines()]
    [dm] = [line for line in logged if line["type"] == "DirectMessage"]
    assert (dm["sender"], dm["username"]) == ("carol", "@p1")
