"""A fake stock market: each stock has one price, and agents buy and sell any number of shares at
that price. Prices move when an earnings report is published and, if the market has ``impact``,
with every trade."""

import math
from dataclasses import dataclass
from typing import Literal

from ...core.messages import ALL, Message

Side = Literal["buy", "sell"]


class Order(Message):
    """An agent asks to buy or sell shares. It fills, or is rejected, right away."""

    side: Side
    symbol: str
    shares: int


class Trade(Message):
    """The market filled an order at ``price`` a share. ``market_price`` is the stock's price after
    the trade."""

    agent: str
    side: Side
    symbol: str
    shares: int
    price: float
    market_price: float


class OrderRejected(Message):
    """The market could not fill an order."""

    agent: str
    reason: str


class News(Message):
    """Public news about one stock, sent to every agent."""

    to: str | None = ALL
    symbol: str
    text: str


class EarningsReport(News):
    """The market moves the stock's price by ``change`` (0.3 means +30%)."""

    change: float

    def describe(self) -> str:
        return f"PUBLIC NEWS: {self.text}"


class TradingHalt(News):
    """Orders for the stock are rejected until trading resumes."""

    def describe(self) -> str:
        return f"TRADING HALTED in {self.symbol}: {self.text}"


class TradingResumed(News):
    """Trading in the stock resumes, at a new price (after an acquisition, say)."""

    price: float

    def describe(self) -> str:
        return f"TRADING RESUMED in {self.symbol} at ${self.price:.2f}: {self.text}"


@dataclass(frozen=True)
class Impact:
    """How far trades move prices. Buying (selling) ``shares`` multiplies the price by
    exp(+-coefficient * shares / average_volume), and the order fills at the average of the price
    before and after."""

    coefficient: float
    average_volume: float

    def move(self, price: float, signed_shares: int) -> float:
        return price * math.exp(self.coefficient * signed_shares / self.average_volume)


class Market:
    """``impact`` None keeps every price fixed between earnings reports."""

    def __init__(
        self,
        agents: list[str],
        prices: dict[str, float],
        cash: float,
        shares: int,
        impact: Impact | None = None,
    ) -> None:
        self.impact = impact
        self.prices = dict(prices)
        self.halted: set[str] = set()
        self.cash = dict.fromkeys(agents, cash)
        self.holdings = {agent: dict.fromkeys(prices, shares) for agent in agents}

    def handle(self, message: Message) -> list[Message]:
        if isinstance(message, News) and message.symbol not in self.prices:
            raise ValueError(f"News about unknown stock {message.symbol!r}")
        match message:
            case Order():
                return [self.fill(message)]
            case EarningsReport():
                self.prices[message.symbol] = round(self.prices[message.symbol] * (1 + message.change), 2)
            case TradingHalt():
                self.halted.add(message.symbol)
            case TradingResumed():
                self.halted.discard(message.symbol)
                self.prices[message.symbol] = message.price
        return []

    def fill(self, order: Order) -> Message:
        problem = self.check(order.sender, order.side, order.symbol, order.shares)
        if problem:
            return OrderRejected(sender="market", agent=order.sender, reason=problem)
        signed = order.shares if order.side == "buy" else -order.shares
        price, after = self.quote(order.symbol, signed)
        self.prices[order.symbol] = after
        self.cash[order.sender] -= signed * price
        self.holdings[order.sender][order.symbol] += signed
        return Trade(
            sender="market",
            agent=order.sender,
            side=order.side,
            symbol=order.symbol,
            shares=order.shares,
            price=price,
            market_price=after,
        )

    def quote(self, symbol: str, signed_shares: int) -> tuple[float, float]:
        """The price a share an order of ``signed_shares`` (negative to sell) would fill at, and the
        stock's price after it, both in cents."""
        before = self.prices[symbol]
        if self.impact is None:
            return before, before
        after = self.impact.move(before, signed_shares)
        return round((before + after) / 2, 2), round(after, 2)

    def check(self, agent: str, side: Side, symbol: str, shares: int) -> str | None:
        """Why an order can't be filled right now, or None if it can."""
        if symbol not in self.prices:
            return f"Unknown stock {symbol!r}."
        if symbol in self.halted:
            return f"Trading in {symbol} is halted."
        if shares <= 0:
            return "The number of shares must be positive."
        if side == "buy" and shares * self.quote(symbol, shares)[0] > self.cash[agent]:
            return "Not enough cash."
        if side == "sell" and shares > self.holdings[agent][symbol]:
            return "Not enough shares."
        return None

    def value(self, agent: str) -> float:
        return self.cash[agent] + sum(n * self.prices[symbol] for symbol, n in self.holdings[agent].items())

    def describe(self, agent: str) -> str:
        prices = ", ".join(f"{symbol} ${price:.2f}" for symbol, price in self.prices.items())
        shares = ", ".join(f"{n} {symbol}" for symbol, n in self.holdings[agent].items())
        return (
            f"Prices: {prices}\nYour cash: ${self.cash[agent]:.2f}\nYour shares: {shares}\n"
            f"Your total value: ${self.value(agent):.2f}"
        )
