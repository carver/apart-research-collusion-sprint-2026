import asyncio

from pydantic_ai.messages import UserPromptPart

from tradingcartel.agents.llm import LLMAgent
from tradingcartel.core.handler import Handler
from tradingcartel.core.messages import Message, Notice
from tradingcartel.core.queue import EventQueue
from tradingcartel.world.messageboard.board import BoardPost, MessageBoard
from tradingcartel.world.messageboard.tools import post_to_board


def make_agents(*names: str) -> list[LLMAgent]:
    return [LLMAgent(name, "test", "You are a test agent.", [post_to_board]) for name in names]


def received(agent: LLMAgent) -> list[str]:
    """The prompts an agent was given, i.e. the messages delivered to it."""
    return [p.content for m in agent.history for p in m.parts if isinstance(p, UserPromptPart)]


def process(queue: EventQueue, message: Message, max_messages: int) -> None:
    queue.put(message)
    asyncio.run(queue.run(max_messages))


def test_a_broadcast_reaches_every_agent_but_the_sender():
    alice, bob, carol = make_agents("alice", "bob", "carol")
    board = MessageBoard()
    queue = EventQueue(Handler([alice, bob, carol], world=[board]).handle)
    post = BoardPost(sender="alice", text="Buy ACME.")

    process(queue, post, max_messages=1)

    assert board.posts == [post]
    assert received(alice) == []
    assert received(bob) == received(carol) == ["alice posted on the message board: Buy ACME."]


def test_a_message_to_one_agent_reaches_only_that_agent():
    alice, bob = make_agents("alice", "bob")
    queue = EventQueue(Handler([alice, bob], world=[]).handle)

    process(queue, Notice(to="bob", text="Hello, Bob."), max_messages=1)

    assert received(alice) == []
    assert received(bob) == ["Hello, Bob."]
