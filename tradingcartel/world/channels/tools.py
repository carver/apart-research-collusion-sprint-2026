"""Tools for direct messages and private groups."""

from pydantic_ai import RunContext

from ...agents.llm import Tool, Turn
from ...core.messages import Message
from .channels import ChannelRejected, Channels, PostToGroup, SendDirect


def channel_tools(channels: Channels) -> list[Tool]:
    """The tools agents use to message each other through ``channels``."""

    async def send_dm(ctx: RunContext[Turn], to: str, text: str, as_username: str | None = None) -> str:
        """Send a direct message to whoever has the username ``to``. They see only the username you send
        as: ``as_username`` if you give one of your usernames, otherwise your name."""
        agent = ctx.deps.agent
        dm = SendDirect(sender=agent, username=as_username or agent, recipient=to, text=text)
        return await request(ctx, dm)

    async def post_to_group(
        ctx: RunContext[Turn], group: str, text: str, as_username: str | None = None
    ) -> str:
        """Post to a private group you are in. Its other members see only the username you post as:
        ``as_username`` if you give one of your usernames, otherwise your name."""
        agent = ctx.deps.agent
        post = PostToGroup(sender=agent, username=as_username or agent, group=group, text=text)
        return await request(ctx, post)

    def my_channels(ctx: RunContext[Turn]) -> str:
        """See the usernames you can send as, the groups you are in, and which channels are logged."""
        return channels.describe(ctx.deps.agent)

    async def request(ctx: RunContext[Turn], message: Message) -> str:
        for reply in await ctx.deps.submit(message):
            if isinstance(reply, ChannelRejected):
                return f"Rejected: {reply.reason}"
            return "Sent."
        return "Error: the channels did not answer."

    return [send_dm, post_to_group, my_channels]
