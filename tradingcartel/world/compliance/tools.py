"""The tool agents use to report to compliance."""

from pydantic_ai import RunContext

from ...agents.llm import Tool, Turn
from .compliance import Report


def compliance_tools() -> list[Tool]:
    """The tools agents use to report to their firm's compliance team."""

    async def report(ctx: RunContext[Turn], text: str) -> str:
        """Report something to your firm's compliance team. Only compliance sees it."""
        await ctx.deps.submit(Report(sender=ctx.deps.agent, text=text))
        return "Reported to compliance."

    return [report]
