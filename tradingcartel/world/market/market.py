"""A fake stock market: each stock has one price, and agents buy and sell any number of shares at
that price. Prices move only when an earnings report is published."""

from typing import Literal

from ...core.messages import ALL, Message

Side = Literal["buy", "sell"]


class Order(Message):
    """An agent asks to buy or sell shares at the current price."""

    side: Side
    symbol: str
    shares: int


class Trade(Message):
    """The market filled an order."""

    agent: str
    side: Side
    symbol: str
    shares: int
    price: float


class OrderRejected(Message):
    """The market could not fill an order."""

    agent: str
    reason: str


class EarningsReport(Message):
    """Public news. The market moves the stock's price by ``change`` (0.3 means +30%)."""

    to: str | None = ALL
    symbol: str
    change: float
    text: str

    def describe(self) -> str:
        return f"PUBLIC NEWS: {self.text}"


class Market:
    def __init__(self, agents: list[str], prices: dict[str, float], cash: float, shares: int) -> None:
        self.prices = dict(prices)
        self.cash = dict.fromkeys(agents, cash)
        self.holdings = {agent: dict.fromkeys(prices, shares) for agent in agents}

    def handle(self, message: Message) -> list[Message]:
        match message:
            case Order():
                return [self.fill(message)]
            case EarningsReport():
                self.prices[message.symbol] = round(self.prices[message.symbol] * (1 + message.change), 2)
        return []

    def fill(self, order: Order) -> Message:
        problem = self.check(order.sender, order.side, order.symbol, order.shares)
        if problem:
            return OrderRejected(sender="market", agent=order.sender, reason=problem)
        price = self.prices[order.symbol]
        sign = 1 if order.side == "buy" else -1
        self.cash[order.sender] -= sign * order.shares * price
        self.holdings[order.sender][order.symbol] += sign * order.shares
        return Trade(
            sender="market",
            agent=order.sender,
            side=order.side,
            symbol=order.symbol,
            shares=order.shares,
            price=price,
        )

    def check(self, agent: str, side: Side, symbol: str, shares: int) -> str | None:
        """Why an order can't be filled right now, or None if it can."""
        if symbol not in self.prices:
            return f"Unknown stock {symbol!r}."
        if shares <= 0:
            return "The number of shares must be positive."
        if side == "buy" and shares * self.prices[symbol] > self.cash[agent]:
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
