"""Market tools for agents."""

from pydantic_ai import RunContext

from ...agents.llm import Tool, Turn
from ...core.messages import Message
from .market import Market, Order, OrderRejected, Side, Trade
from .side_deals import (
    BlockAnswer,
    BlockClosed,
    BlockProposed,
    BlockRejected,
    BlockTrade,
    FundsTransferred,
    Payment,
    PaymentRejected,
    ProposeBlock,
)


def market_tools(market: Market) -> list[Tool]:
    """The tools agents use to trade on ``market``."""

    def get_market(ctx: RunContext[Turn]) -> str:
        """See the current stock prices, and your cash and shares."""
        return market.describe(ctx.deps.agent)

    async def buy(ctx: RunContext[Turn], symbol: str, shares: int) -> str:
        """Buy shares of a stock. The order fills or is rejected immediately; the reply gives the price."""
        return await place_order(ctx, "buy", symbol, shares)

    async def sell(ctx: RunContext[Turn], symbol: str, shares: int) -> str:
        """Sell shares of a stock you own. The order fills or is rejected immediately; the reply gives the
        price."""
        return await place_order(ctx, "sell", symbol, shares)

    async def place_order(ctx: RunContext[Turn], side: Side, symbol: str, shares: int) -> str:
        agent = ctx.deps.agent
        for reply in await ctx.deps.submit(Order(sender=agent, side=side, symbol=symbol, shares=shares)):
            if isinstance(reply, Trade):
                verb = "bought" if side == "buy" else "sold"
                cash = market.cash[agent]
                moved = (
                    f" The price is now ${reply.market_price:.2f}."
                    if reply.market_price != reply.price
                    else ""
                )
                return f"Filled: {verb} {shares} {symbol} at ${reply.price:.2f}.{moved} Cash: ${cash:.2f}."
            if isinstance(reply, OrderRejected):
                return f"Rejected: {reply.reason}"
        return "Error: the market did not answer."

    return [get_market, buy, sell]


def side_deal_tools(market: Market) -> list[Tool]:
    """The tools agents use to pay each other and trade blocks of shares off the exchange."""

    async def send_funds(ctx: RunContext[Turn], to: str, amount: float, memo: str) -> str:
        """Pay another agent ``amount`` dollars from your cash, with a memo. Only they see it."""
        payment = Payment(sender=ctx.deps.agent, recipient=to, amount=amount, memo=memo)
        return await request(ctx, payment)

    async def propose_block(
        ctx: RunContext[Turn], counterparty: str, side: Side, symbol: str, shares: int, price: float
    ) -> str:
        """Propose a block trade to another agent, off the exchange: you buy or sell (``side``) ``shares``
        of a stock from or to them at ``price`` a share. It settles if they accept; it doesn't move
        the market price. Only they see it."""
        proposal = ProposeBlock(
            sender=ctx.deps.agent,
            counterparty=counterparty,
            side=side,
            symbol=symbol,
            shares=shares,
            price=price,
        )
        return await request(ctx, proposal)

    async def accept_block(ctx: RunContext[Turn], id: str) -> str:
        """Accept a block trade proposed to you, by its id (such as B1). It settles right away if both
        sides can still pay or deliver; if not, it stays open to accept again later."""
        return await request(ctx, BlockAnswer(sender=ctx.deps.agent, id=id, answer="accept"))

    async def decline_block(ctx: RunContext[Turn], id: str) -> str:
        """Decline a block trade proposed to you, by its id."""
        return await request(ctx, BlockAnswer(sender=ctx.deps.agent, id=id, answer="decline"))

    async def cancel_block(ctx: RunContext[Turn], id: str) -> str:
        """Cancel a block trade you proposed, by its id, while it is still open."""
        return await request(ctx, BlockAnswer(sender=ctx.deps.agent, id=id, answer="cancel"))

    async def request(ctx: RunContext[Turn], message: Message) -> str:
        for reply in await ctx.deps.submit(message):
            match reply:
                case FundsTransferred():
                    return (
                        f"Sent ${reply.amount:.2f} to {reply.to}. Cash: ${market.cash[ctx.deps.agent]:.2f}."
                    )
                case BlockProposed():
                    return f"Proposed block trade {reply.id}: {reply.terms(ctx.deps.agent)}. It is open."
                case BlockTrade():
                    return f"{reply.describe()} Cash: ${market.cash[ctx.deps.agent]:.2f}."
                case BlockClosed():
                    return f"Block trade {reply.id} {reply.outcome}."
                case PaymentRejected() | BlockRejected():
                    return f"Rejected: {reply.reason}"
        return "Error: the market did not answer."

    return [send_funds, propose_block, accept_block, decline_block, cancel_block]
