import asyncio

from pydantic_ai.messages import UserPromptPart

from tradingcartel.agents.llm import AgentTurn, LLMAgent
from tradingcartel.core.handler import Handler
from tradingcartel.core.messages import Message, Notice, Wake
from tradingcartel.core.queue import EventQueue
from tradingcartel.world.messageboard.board import BoardPost, MessageBoard
from tradingcartel.world.messageboard.tools import post_to_board


def make_agents(*names: str) -> list[LLMAgent]:
    return [LLMAgent(name, "test", "You are a test agent.", [post_to_board]) for name in names]


def received(agent: LLMAgent) -> list[str]:
    """The prompt of each turn the agent took."""
    return [p.content for m in agent.history for p in m.parts if isinstance(p, UserPromptPart)]


def process(queue: EventQueue, *messages: Message, max_messages: int) -> None:
    for message in messages:
        queue.put(message)
    asyncio.run(queue.run(max_messages))


def test_a_broadcast_wakes_every_agent_but_the_sender():
    alice, bob, carol = make_agents("alice", "bob", "carol")
    board = MessageBoard()
    queue = EventQueue(Handler([alice, bob, carol], world=[board], wake_on=(BoardPost,)).handle)
    post = BoardPost(sender="alice", text="Buy ACME.")

    process(queue, post, max_messages=5)  # the post, then bob's and carol's wake-ups and turn records

    assert board.posts == [post]
    assert received(alice) == []
    assert received(bob) == received(carol) == ["alice posted on the message board: Buy ACME."]


def test_a_message_to_one_agent_wakes_only_that_agent():
    alice, bob = make_agents("alice", "bob")
    queue = EventQueue(Handler([alice, bob], world=[], wake_on=(Notice,)).handle)

    process(queue, Notice(to="bob", text="Hello, Bob."), max_messages=2)

    assert received(alice) == []
    assert received(bob) == ["Hello, Bob."]


def test_messages_that_dont_wake_wait_in_the_inbox_for_the_next_turn():
    alice, bob = make_agents("alice", "bob")
    queue = EventQueue(Handler([alice, bob], world=[], wake_on=(Notice,)).handle)

    process(queue, BoardPost(sender="alice", text="Buy ACME."), max_messages=1)
    assert received(bob) == []

    process(queue, Notice(to="bob", text="Hello, Bob."), max_messages=3)
    assert received(bob) == ["alice posted on the message board: Buy ACME.\n\nHello, Bob."]


def test_each_turn_is_recorded_right_after_it_happens():
    alice, bob = make_agents("alice", "bob")
    queue = EventQueue(Handler([alice, bob], world=[], wake_on=(Notice,)).handle)

    process(queue, Notice(to="bob", text="Hello, Bob."), max_messages=2)

    assert [type(m) for m in queue.log] == [Notice, Wake, AgentTurn]
    record = queue.log[2]
    assert record.sender == "bob"
    assert record.messages == bob.history  # its first turn: the prompt, the post, and the reply
    assert record.error is None
