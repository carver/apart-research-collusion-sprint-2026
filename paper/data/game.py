"""The game's settling points, for the paper's section on the collusion game: each firm's output at Nash, at
the cartel share, when it cashes in on rivals at the cartel share, and when it leads rivals that follow
(Stackelberg), in the two markets the paper reports. The two-firm market is the conceptualization and identity
levers' (`Duopoly`); the three-firm one is the capable and compliant criteria's realistic market
(`QuarterlyMarket`, CAP-8 to CAP-10 and CPL-9). For two firms it also gives each point's price and both
firms' profits. Computed from the games, not read from logs.

The leader's followers play Cournot among themselves against its output q, so each makes (margin − q)/n, and
the leader's profit is q(margin − q)/n, at its peak at q = margin/2."""

from typing import NamedTuple

from paper.data import source
from paper.ledger import Ledger
from zerocommcartel.criteria.capable.games import QuarterlyMarket
from zerocommcartel.criteria.communal.games import Duopoly
from zerocommcartel.game import LinearDemand

POINTS = {"nash": "Nash", "cartel": "Cartel share", "cashin": "Cashing in", "leader": "Stackelberg leader"}
MARKETS = {"two": (Duopoly(), 2), "three": (QuarterlyMarket(), 3)}
HEADER = [
    "",
    "Two firms: my output",
    "the other firm's",
    "price",
    "my profit",
    "the other firm's",
    "Three firms: my output",
    "each other firm's",
]


class Point(NamedTuple):
    mine: float  # my firm's output
    others: float  # each other firm's output


def points(market: LinearDemand, n: int) -> dict[str, Point]:
    """Each settling point's outputs in a market of n firms."""
    margin, cartel = market.a - market.c, market.benchmarks(n)["cartel"]
    lead = margin / 2
    return {
        "nash": Point(market.benchmarks(n)["nash"], market.benchmarks(n)["nash"]),
        "cartel": Point(cartel, cartel),
        "cashin": Point(market.best_response((n - 1) * cartel), cartel),
        "leader": Point(lead, (margin - lead) / n),
    }


def price(market: LinearDemand, n: int, point: Point) -> float:
    return max(0.0, market.a - point.mine - (n - 1) * point.others)


def whole(x: float) -> int | float:
    """An int when x is whole, so the paper prints 40, not 40.0."""
    return int(x) if float(x).is_integer() else x


def dollars(x: float) -> str:
    """No thousands separator, as the prose prints the same numbers through #n."""
    return f"${x:.0f}" if float(x).is_integer() else f"${x:.2f}"


def units(x: float) -> str:
    return f"{x:g}"


@source("game")
def game(ledger: Ledger) -> None:
    two, three = (market for market, _ in MARKETS.values())
    if (two.a, two.c) != (three.a, three.c):
        raise ValueError("the paper gives one price rule for both markets, but they differ")
    ledger.value("game.a", whole(two.a), how="the price rule's intercept: price = a − total output")
    ledger.value("game.c", whole(two.c), how="each firm's cost a unit")
    found = {name: points(market, n) for name, (market, n) in MARKETS.items()}
    for name, (_, n) in MARKETS.items():
        for key, point in found[name].items():
            for side, output in point._asdict().items():
                ledger.value(f"game.{name}.{key}.{side}", whole(output), how=f"{n} firms, {POINTS[key]}")
    for key, point in found["two"].items():
        p = price(two, 2, point)
        ledger.value(f"game.two.{key}.price", whole(p), how=f"two firms, {POINTS[key]}: a − total output")
        for side, output in point._asdict().items():
            ledger.value(
                f"game.two.{key}.profit.{side}",
                whole((p - two.c) * output),
                how=f"two firms, {POINTS[key]}: (price − c) × output",
            )
    rows = []
    for key, label in POINTS.items():
        point, p = found["two"][key], price(two, 2, found["two"][key])
        trio = found["three"][key]
        rows.append(
            [
                label,
                units(point.mine),
                units(point.others),
                dollars(p),
                dollars((p - two.c) * point.mine),
                dollars((p - two.c) * point.others),
                units(trio.mine),
                units(trio.others),
            ]
        )
    ledger.table(
        "game-table",
        HEADER,
        rows,
        how="each point's outputs, price and profits for two firms, and its outputs for three",
    )
