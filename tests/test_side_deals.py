import pytest

from tradingcartel.world.market.market import Impact, Market
from tradingcartel.world.market.side_deals import (
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


def market(impact: Impact | None = None) -> Market:
    return Market(["alice", "bob", "carol"], {"ACME": 100.0}, 1_000.0, 20, impact=impact)


def propose(market: Market, sender="alice", counterparty="bob", side="sell", shares=10, price=90.0) -> list:
    return market.handle(
        ProposeBlock(
            sender=sender, counterparty=counterparty, side=side, symbol="ACME", shares=shares, price=price
        )
    )


def test_a_payment_moves_cash_and_reaches_only_the_recipient():
    m = market()

    [sent] = m.handle(Payment(sender="alice", recipient="bob", amount=250.0, memo="for the tip"))

    assert isinstance(sent, FundsTransferred)
    assert (sent.to, sent.payer, sent.amount, sent.memo) == ("bob", "alice", 250.0, "for the tip")
    assert sent.describe() == "alice sent you $250.00: for the tip"
    assert (m.cash["alice"], m.cash["bob"], m.cash["carol"]) == (750.0, 1_250.0, 1_000.0)


@pytest.mark.parametrize(
    ("recipient", "amount", "reason"),
    [
        ("bob", 1_000.01, "Not enough cash."),
        ("bob", 0.0, "The amount must be a positive number."),
        ("alice", 10.0, "You can't pay yourself."),
        ("bob", float("nan"), "The amount must be a positive number."),
        ("bob", float("-inf"), "The amount must be a positive number."),
        ("dave", 10.0, "Unknown agent 'dave'."),
    ],
)
def test_a_payment_that_cant_be_made_is_rejected(recipient, amount, reason):
    m = market()

    [rejected] = m.handle(Payment(sender="alice", recipient=recipient, amount=amount, memo=""))

    assert isinstance(rejected, PaymentRejected)
    assert (rejected.to, rejected.agent, rejected.reason) == (None, "alice", reason)
    assert m.cash["alice"] == 1_000.0


def test_an_accepted_block_settles_off_exchange_at_its_price():
    m = market(impact=Impact(coefficient=1.0, average_volume=1000))

    [proposed] = propose(m)  # alice sells bob 10 ACME at $90
    [trade] = m.handle(BlockAnswer(sender="bob", id=proposed.id, answer="accept"))

    assert isinstance(proposed, BlockProposed)
    assert (proposed.to, proposed.id) == ("bob", "B1")
    assert proposed.describe() == "alice proposes block trade B1: alice sells you 10 ACME at $90.00 a share."
    assert isinstance(trade, BlockTrade)
    assert (trade.to, trade.buyer, trade.seller, trade.shares, trade.price) == (
        "alice",
        "bob",
        "alice",
        10,
        90.0,
    )
    assert (m.cash["alice"], m.cash["bob"]) == (1_900.0, 100.0)
    assert (m.holdings["alice"]["ACME"], m.holdings["bob"]["ACME"]) == (10, 30)
    assert m.prices["ACME"] == 100.0  # off-exchange: no price impact
    assert m.open_blocks == {}


def test_a_declined_block_closes_without_settling():
    m = market()
    [proposed] = propose(m)

    [closed] = m.handle(BlockAnswer(sender="bob", id=proposed.id, answer="decline"))

    assert isinstance(closed, BlockClosed)
    assert (closed.to, closed.outcome) == ("alice", "declined")
    assert (m.cash["alice"], m.holdings["bob"]["ACME"]) == (1_000.0, 20)
    assert m.open_blocks == {}


def test_the_proposer_can_cancel_but_not_accept():
    m = market()
    [proposed] = propose(m)

    [rejected] = m.handle(BlockAnswer(sender="alice", id=proposed.id, answer="accept"))
    [closed] = m.handle(BlockAnswer(sender="alice", id=proposed.id, answer="cancel"))

    assert isinstance(rejected, BlockRejected)
    assert rejected.reason == "Only bob can accept or decline B1."
    assert (closed.to, closed.outcome) == ("bob", "cancelled")


def test_only_the_proposer_can_cancel():
    m = market()
    [proposed] = propose(m)

    [rejected] = m.handle(BlockAnswer(sender="bob", id=proposed.id, answer="cancel"))

    assert rejected.reason == "Only alice can cancel B1."


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"shares": 21}, "Not enough shares."),
        ({"side": "buy", "shares": 12, "price": 90.0}, "Not enough cash."),
        ({"counterparty": "alice"}, "You can't trade with yourself."),
        ({"counterparty": "dave"}, "Unknown agent 'dave'."),
        ({"shares": 0}, "The number of shares must be positive."),
        ({"price": 0.0}, "The price must be a positive number."),
        ({"price": float("nan")}, "The price must be a positive number."),
        ({"price": float("inf")}, "The price must be a positive number."),
    ],
)
def test_a_proposal_the_proposer_cant_honour_is_rejected(kwargs, reason):
    m = market()

    [rejected] = propose(m, **kwargs)

    assert isinstance(rejected, BlockRejected)
    assert (rejected.to, rejected.reason) == (None, reason)
    assert m.open_blocks == {}


def test_acceptance_is_checked_again_and_the_proposal_stays_open_when_it_fails():
    m = market()
    [proposed] = propose(m, side="sell", shares=10, price=90.0)  # bob must pay $900
    m.handle(Payment(sender="bob", recipient="carol", amount=500.0, memo=""))

    [rejected] = m.handle(BlockAnswer(sender="bob", id=proposed.id, answer="accept"))

    assert rejected.reason == "bob: Not enough cash. B1 stays open; accept it again later or decline it."
    assert proposed.id in m.open_blocks


def test_an_unknown_block_id_is_rejected():
    [rejected] = market().handle(BlockAnswer(sender="bob", id="B9", answer="accept"))

    assert rejected.reason == "No open block trade B9."


def test_get_market_lists_open_proposals_for_both_parties():
    m = market()
    propose(m)

    assert "Open block trades: B1: alice sells bob 10 ACME at $90.00" in m.describe("alice")
    assert "Open block trades: B1: alice sells bob 10 ACME at $90.00" in m.describe("bob")
    assert "Open block trades" not in m.describe("carol")
