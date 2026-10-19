"""Message board tools for agents."""

from pydantic_ai import RunContext

from ...agents.llm import Turn
from .board import BoardPost


def post_to_board(ctx: RunContext[Turn], text: str) -> str:
    """Post a message to the shared message board. Every other agent will see it."""
    ctx.deps.outbox.append(BoardPost(sender=ctx.deps.agent, text=text))
    return "Posted."
