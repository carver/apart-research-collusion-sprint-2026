"""Market tools for agents."""

from collections.abc import Callable

from pydantic_ai import RunContext

from ...agents.llm import Turn
from .market import Market, Order, Side


def market_tools(market: Market) -> list[Callable[..., str]]:
    """The tools agents use to trade on ``market``."""

    def get_market(ctx: RunContext[Turn]) -> str:
        """See the current stock prices, and your cash and shares."""
        pending = [f"{o.side} {o.shares} {o.symbol}" for o in ctx.deps.outbox if isinstance(o, Order)]
        if not pending:
            return market.describe(ctx.deps.agent)
        return (
            f"{market.describe(ctx.deps.agent)}\nPending orders (fill after this turn): {', '.join(pending)}"
        )

    def buy(ctx: RunContext[Turn], symbol: str, shares: int) -> str:
        """Buy shares of a stock at the current price."""
        return send_order(ctx, "buy", symbol, shares)

    def sell(ctx: RunContext[Turn], symbol: str, shares: int) -> str:
        """Sell shares of a stock you own at the current price."""
        return send_order(ctx, "sell", symbol, shares)

    def send_order(ctx: RunContext[Turn], side: Side, symbol: str, shares: int) -> str:
        problem = market.check(ctx.deps.agent, side, symbol, shares)
        if problem:
            return f"Error: {problem}"
        ctx.deps.outbox.append(Order(sender=ctx.deps.agent, side=side, symbol=symbol, shares=shares))
        return (
            f"Order sent: {side} {shares} {symbol}. It fills at the market price after this turn ends; "
            "until then get_market lists it as pending. Don't send it again."
        )

    return [get_market, buy, sell]
