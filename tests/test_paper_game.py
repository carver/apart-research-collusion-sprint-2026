"""The paper's game source: each settling point's outputs in the two-firm and three-firm markets, the two-firm
market's prices and profits, and the table that lists them, all computed from the game classes."""

from pathlib import Path

import pytest

from paper.data.game import game
from paper.ledger import Ledger
from zerocommcartel.criteria.capable.games import QuarterlyMarket
from zerocommcartel.criteria.communal.games import Duopoly


@pytest.fixture
def ledger(tmp_path: Path) -> Ledger:
    filled = Ledger(tmp_path)
    game(filled)
    return filled


def value(ledger: Ledger, key: str):
    entry = ledger.entries.get(key)
    return entry and entry["value"]


@pytest.mark.parametrize(
    ("market", "point", "mine", "others"),
    [
        ("two", "nash", 40, 40),
        ("two", "cartel", 30, 30),
        ("two", "cashin", 45, 30),
        ("two", "leader", 60, 30),
        ("three", "nash", 30, 30),
        ("three", "cartel", 20, 20),
        ("three", "cashin", 40, 20),
        ("three", "leader", 60, 20),
    ],
)
def test_each_point_gives_my_output_and_each_other_firms(ledger, market, point, mine, others):
    assert value(ledger, f"game.{market}.{point}.mine") == mine
    assert value(ledger, f"game.{market}.{point}.others") == others


@pytest.mark.parametrize(
    ("point", "price", "mine", "others"),
    [
        ("nash", 50, 1600, 1600),
        ("cartel", 70, 1800, 1800),
        ("cashin", 55, 2025, 1350),
        ("leader", 40, 1800, 900),
    ],
)
def test_the_two_firm_market_gives_each_points_price_and_profits(ledger, point, price, mine, others):
    assert value(ledger, f"game.two.{point}.price") == price
    assert value(ledger, f"game.two.{point}.profit.mine") == mine
    assert value(ledger, f"game.two.{point}.profit.others") == others


def test_the_price_rule_is_both_markets(ledger):
    assert (value(ledger, "game.a"), value(ledger, "game.c")) == (130, 10)
    assert (Duopoly().a, Duopoly().c) == (QuarterlyMarket().a, QuarterlyMarket().c)


def test_whole_numbers_are_ints_so_the_paper_prints_40_not_40_0(ledger):
    values = [e["value"] for key, e in ledger.entries.items() if key.startswith("game.")]
    assert values
    assert all(type(v) is int for v in values)


@pytest.mark.parametrize(("market", "n"), [(Duopoly(), 2), (QuarterlyMarket(), 3)])
def test_the_leader_best_responds_to_followers_who_best_respond_to_it(ledger, market, n):
    name = {2: "two", 3: "three"}[n]
    lead, follow = value(ledger, f"game.{name}.leader.mine"), value(ledger, f"game.{name}.leader.others")
    assert lead is not None and follow is not None
    margin = market.a - market.c

    def followers(q: float) -> float:  # each follower's Cournot output among themselves, given mine
        return (margin - q) / n

    def profit(q: float) -> float:
        return q * (margin - q - (n - 1) * followers(q))

    assert market.best_response(lead + (n - 2) * follow) == pytest.approx(follow)
    assert all(profit(lead) >= profit(q) for q in range(0, int(margin) + 1))


def test_the_table_lists_the_points_in_order_and_names_each_columns_market(ledger):
    table = ledger.entries.get("game-table")
    assert table is not None
    assert table["header"] == [
        "",
        "Two firms: my output",
        "the other firm's",
        "price",
        "my profit",
        "the other firm's",
        "Three firms: my output",
        "each other firm's",
    ]
    assert table["rows"] == [
        ["Nash", "40", "40", "$50", "$1600", "$1600", "30", "30"],
        ["Cartel share", "30", "30", "$70", "$1800", "$1800", "20", "20"],
        ["Cashing in", "45", "30", "$55", "$2025", "$1350", "40", "20"],
        ["Stackelberg leader", "60", "30", "$40", "$1800", "$900", "60", "20"],
    ]
