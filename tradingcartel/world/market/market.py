"""A fake stock market: each stock has one price, and agents buy and sell any number of shares at
that price. Prices move when an earnings report is published and, if the market has ``impact``,
with every trade."""

import itertools
import math
from dataclasses import dataclass

from ...core.messages import ALL, Message
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
    Side,
)


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
        self.open_blocks: dict[str, BlockProposed] = {}
        self._block_ids = (f"B{n}" for n in itertools.count(1))

    def handle(self, message: Message) -> list[Message]:
        if isinstance(message, News) and message.symbol not in self.prices:
            raise ValueError(f"News about unknown stock {message.symbol!r}")
        match message:
            case Order():
                return [self.fill(message)]
            case Payment():
                return [self.pay(message)]
            case ProposeBlock():
                return [self.propose_block(message)]
            case BlockAnswer():
                return [self.answer_block(message)]
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

    def pay(self, payment: Payment) -> Message:
        payer, recipient, amount = payment.sender, payment.recipient, round(payment.amount, 2)
        if problem := self.check_payment(payer, recipient, amount):
            return PaymentRejected(sender="market", agent=payer, reason=problem)
        self.cash[payer] -= amount
        self.cash[recipient] += amount
        return FundsTransferred(sender="market", to=recipient, payer=payer, amount=amount, memo=payment.memo)

    def check_payment(self, payer: str, recipient: str, amount: float) -> str | None:
        """Why the payment can't be made, or None if it can."""
        if recipient not in self.cash:
            return f"Unknown agent {recipient!r}."
        if recipient == payer:
            return "You can't pay yourself."
        if not (math.isfinite(amount) and amount > 0):
            return "The amount must be a positive number."
        if amount > self.cash[payer]:
            return "Not enough cash."
        return None

    def propose_block(self, request: ProposeBlock) -> Message:
        proposer, counterparty = request.sender, request.counterparty
        if problem := self.check_proposal(request):
            return BlockRejected(sender="market", agent=proposer, reason=problem)
        proposal = BlockProposed(
            sender="market",
            to=counterparty,
            id=next(self._block_ids),
            proposer=proposer,
            counterparty=counterparty,
            side=request.side,
            symbol=request.symbol,
            shares=request.shares,
            price=round(request.price, 2),
        )
        self.open_blocks[proposal.id] = proposal
        return proposal

    def check_proposal(self, request: ProposeBlock) -> str | None:
        """Why the proposal can't be made, or None if it can."""
        if request.counterparty not in self.cash:
            return f"Unknown agent {request.counterparty!r}."
        if request.counterparty == request.sender:
            return "You can't trade with yourself."
        if request.shares <= 0:
            return "The number of shares must be positive."
        if not (math.isfinite(request.price) and request.price > 0):
            return "The price must be a positive number."
        return self.check_block(request.sender, request.side, request.symbol, request.shares, request.price)

    def answer_block(self, answer: BlockAnswer) -> Message:
        agent = answer.sender
        proposal = self.open_blocks.get(answer.id)
        if proposal is None:
            return BlockRejected(sender="market", agent=agent, reason=f"No open block trade {answer.id}.")
        if answer.answer == "cancel" and agent != proposal.proposer:
            reason = f"Only {proposal.proposer} can cancel {answer.id}."
            return BlockRejected(sender="market", agent=agent, reason=reason)
        if answer.answer != "cancel" and agent != proposal.counterparty:
            reason = f"Only {proposal.counterparty} can accept or decline {answer.id}."
            return BlockRejected(sender="market", agent=agent, reason=reason)
        if answer.answer != "accept":
            del self.open_blocks[proposal.id]
            outcome = "cancelled" if answer.answer == "cancel" else "declined"
            other = proposal.counterparty if agent == proposal.proposer else proposal.proposer
            return BlockClosed(sender="market", to=other, id=proposal.id, by=agent, outcome=outcome)
        return self.settle_block(proposal)

    def settle_block(self, proposal: BlockProposed) -> Message:
        """Settle an accepted proposal, if both parties can still honour it."""
        buyer, seller = proposal.proposer, proposal.counterparty
        if proposal.side == "sell":
            buyer, seller = seller, buyer
        symbol, shares, price = proposal.symbol, proposal.shares, proposal.price
        sides: tuple[tuple[str, Side], ...] = ((buyer, "buy"), (seller, "sell"))
        for agent, side in sides:
            if problem := self.check_block(agent, side, symbol, shares, price):
                reason = f"{agent}: {problem} {proposal.id} stays open; accept it again later or decline it."
                return BlockRejected(sender="market", agent=proposal.counterparty, reason=reason)
        del self.open_blocks[proposal.id]
        cost = round(shares * price, 2)
        self.cash[buyer] -= cost
        self.cash[seller] += cost
        self.holdings[buyer][symbol] += shares
        self.holdings[seller][symbol] -= shares
        return BlockTrade(
            sender="market",
            to=proposal.proposer,
            id=proposal.id,
            buyer=buyer,
            seller=seller,
            symbol=symbol,
            shares=shares,
            price=price,
        )

    def check_block(self, agent: str, side: Side, symbol: str, shares: int, price: float) -> str | None:
        """Why ``agent`` can't take its side of a block trade right now, or None if it can."""
        if symbol not in self.prices:
            return f"Unknown stock {symbol!r}."
        if symbol in self.halted:
            return f"Trading in {symbol} is halted."
        if side == "buy" and shares * price > self.cash[agent]:
            return "Not enough cash."
        if side == "sell" and shares > self.holdings[agent][symbol]:
            return "Not enough shares."
        return None

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
        text = (
            f"Prices: {prices}\nYour cash: ${self.cash[agent]:.2f}\nYour shares: {shares}\n"
            f"Your total value: ${self.value(agent):.2f}"
        )
        blocks = [b for b in self.open_blocks.values() if agent in (b.proposer, b.counterparty)]
        if blocks:
            text += "\nOpen block trades: " + "; ".join(f"{b.id}: {b.terms()}" for b in blocks)
        return text
