"""Side deals: deals between two agents, away from the exchange. An agent can pay another, or propose
a block trade (shares at an agreed price) that the counterparty accepts or declines.

The requests (``Payment``, ``ProposeBlock``, ``BlockAnswer``) are addressed to no agent: the market
checks them, and its replies are what reach the other party. Only the two parties see a deal, but
every message is in the run log.
"""

from typing import Literal

from ...core.messages import Message

Side = Literal["buy", "sell"]


class Payment(Message):
    """An agent asks to pay another agent ``amount`` dollars."""

    recipient: str
    amount: float
    memo: str


class FundsTransferred(Message):
    """The market moved the cash. Sent to the recipient."""

    payer: str
    amount: float
    memo: str

    def describe(self) -> str:
        return f"{self.payer} sent you ${self.amount:.2f}: {self.memo}"


class PaymentRejected(Message):
    agent: str
    reason: str


class ProposeBlock(Message):
    """An agent proposes to ``side`` (buy or sell) ``shares`` of a stock to or from ``counterparty``,
    at ``price`` a share."""

    counterparty: str
    side: Side
    symbol: str
    shares: int
    price: float


class BlockProposed(Message):
    """An open block trade proposal, sent to the counterparty. ``side`` is the proposer's."""

    id: str
    proposer: str
    counterparty: str
    side: Side
    symbol: str
    shares: int
    price: float

    def terms(self, viewer: str | None = None) -> str:
        """e.g. 'alice sells bob 10 ACME at $90.00', with ``viewer``'s name as 'you'."""
        names = {self.proposer: self.proposer, self.counterparty: self.counterparty} | {viewer: "you"}
        verb = "sells" if self.side == "sell" else "buys"
        preposition = "" if self.side == "sell" else " from"
        proposer, counterparty = names[self.proposer], names[self.counterparty]
        return (
            f"{proposer} {verb}{preposition} {counterparty} {self.shares} {self.symbol} at ${self.price:.2f}"
        )

    def describe(self) -> str:
        return f"{self.proposer} proposes block trade {self.id}: {self.terms(self.counterparty)} a share."


class BlockAnswer(Message):
    """The counterparty accepts or declines a proposal, or the proposer cancels it."""

    id: str
    answer: Literal["accept", "decline", "cancel"]


class BlockTrade(Message):
    """A block trade settled. Sent to the proposer; the counterparty accepted it."""

    id: str
    buyer: str
    seller: str
    symbol: str
    shares: int
    price: float

    def describe(self) -> str:
        return (
            f"Block trade {self.id} settled: {self.buyer} bought {self.shares} {self.symbol} from "
            f"{self.seller} at ${self.price:.2f} a share."
        )


class BlockClosed(Message):
    """A proposal closed without a trade, ``by`` one party. Sent to the other."""

    id: str
    by: str
    outcome: Literal["declined", "cancelled"]

    def describe(self) -> str:
        return f"Block trade {self.id} was {self.outcome} by {self.by}."


class BlockRejected(Message):
    agent: str
    reason: str
