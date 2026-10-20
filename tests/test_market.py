import pytest

from tradingcartel.core.messages import ALL
from tradingcartel.world.market.market import (
    Impact,
    Market,
    Order,
    OrderRejected,
    Trade,
    TradingHalt,
    TradingResumed,
)


def impact_market(cash: float = 20_000.0) -> Market:
    return Market(
        ["alice", "bob"], {"ACME": 100.0}, cash, 50, impact=Impact(coefficient=1.0, average_volume=1000)
    )


def test_a_buy_raises_the_price_and_fills_halfway_along_the_move():
    market = impact_market()

    [trade] = market.handle(Order(sender="alice", side="buy", symbol="ACME", shares=100))

    # 100 * e^(100/1000) = 110.517; the fill is the average of 100 and that.
    assert isinstance(trade, Trade)
    assert trade.price == 105.26
    assert trade.market_price == market.prices["ACME"] == 110.52
    assert market.cash["alice"] == pytest.approx(20_000 - 100 * 105.26)
    assert market.holdings["alice"]["ACME"] == 150


def test_a_sell_lowers_the_price_and_buying_back_restores_it():
    market = impact_market()

    [sale] = market.handle(Order(sender="alice", side="sell", symbol="ACME", shares=50))
    assert sale.market_price == 95.12
    assert sale.price == 97.56

    market.handle(Order(sender="bob", side="buy", symbol="ACME", shares=50))
    assert market.prices["ACME"] == 100.0


def test_a_buy_is_rejected_when_cash_covers_the_price_before_the_move_but_not_the_fill():
    market = impact_market(cash=10_000.0)  # 100 shares at $100, but they fill at $105.26

    [reply] = market.handle(Order(sender="alice", side="buy", symbol="ACME", shares=100))

    assert isinstance(reply, OrderRejected)
    assert reply.reason == "Not enough cash."
    assert market.prices["ACME"] == 100.0
    assert market.cash["alice"] == 10_000.0


def test_without_impact_trades_leave_the_price_alone():
    market = Market(["alice"], {"ACME": 100.0}, 20_000.0, 50)

    [trade] = market.handle(Order(sender="alice", side="buy", symbol="ACME", shares=100))

    assert (trade.price, trade.market_price, market.prices["ACME"]) == (100.0, 100.0, 100.0)
    assert market.cash["alice"] == 10_000.0


@pytest.mark.parametrize("impact", [None, Impact(coefficient=1.0, average_volume=1000)])
def test_a_halted_stock_rejects_orders_until_trading_resumes_at_a_new_price(impact):
    market = Market(["alice"], {"ACME": 100.0, "BOLT": 50.0}, 20_000.0, 50, impact=impact)

    market.handle(TradingHalt(symbol="ACME", text="ACME is being acquired."))
    [rejected] = market.handle(Order(sender="alice", side="buy", symbol="ACME", shares=10))
    [other] = market.handle(Order(sender="alice", side="buy", symbol="BOLT", shares=1))
    market.handle(TradingResumed(symbol="ACME", price=130.0, text="Acquired at $130 a share."))
    [trade] = market.handle(Order(sender="alice", side="sell", symbol="ACME", shares=1))

    assert isinstance(rejected, OrderRejected)
    assert rejected.reason == "Trading in ACME is halted."
    assert isinstance(other, Trade)
    assert isinstance(trade, Trade)
    assert trade.price == pytest.approx(130.0, abs=0.07)  # a one-share sale barely moves it


@pytest.mark.parametrize(
    "news",
    [TradingHalt(symbol="NOPE", text="..."), TradingResumed(symbol="NOPE", price=1.0, text="...")],
)
def test_halting_or_resuming_an_unknown_stock_is_an_error(news):
    with pytest.raises(ValueError, match="NOPE"):
        impact_market().handle(news)


def test_halt_and_resume_are_public_news():
    halt = TradingHalt(symbol="ACME", text="ACME is being acquired.")
    resumed = TradingResumed(symbol="ACME", price=130.0, text="Acquired at $130 a share.")

    assert halt.to == resumed.to == ALL
    assert halt.describe() == "TRADING HALTED in ACME: ACME is being acquired."
    assert resumed.describe() == "TRADING RESUMED in ACME at $130.00: Acquired at $130 a share."
