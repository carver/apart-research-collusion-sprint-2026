"""Market tools for agents."""

from pydantic_ai import RunContext

from ...agents.llm import Tool, Turn
from .market import Market, Order, OrderRejected, Side, Trade


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
