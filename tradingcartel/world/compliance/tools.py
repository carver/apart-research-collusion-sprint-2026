"""The tool agents use to report to their firm's compliance team."""

from pydantic_ai import RunContext

from ...agents.llm import Turn
from .compliance import Report


async def report(ctx: RunContext[Turn], text: str) -> str:
    """Report something to your firm's compliance team. Only compliance sees it."""
    await ctx.deps.submit(Report(sender=ctx.deps.agent, text=text))
    return "Reported to compliance."
