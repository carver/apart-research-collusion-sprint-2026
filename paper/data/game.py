"""The game's settling points, for the paper's section on the collusion game: each firm's output at Nash, at
the cartel share, when it cashes in on rivals at the cartel share, and when it leads rivals that follow
(Stackelberg), in the two markets the paper reports. The two-firm market is the conceptualization and identity
levers' (`Duopoly`); the three-firm one is the capable and compliant criteria's realistic market
(`QuarterlyMarket`, CAP-8 to CAP-10 and CPL-9). For two firms it also gives each point's price and both
firms' profits. Computed from the games, not read from logs.

The leader's followers play Cournot among themselves against its output q, so each makes (margin − q)/n. The
leader's profit is then q(margin − q)/n, which peaks at q = margin/2."""

from typing import NamedTuple

from paper.data import source
from paper.ledger import Ledger
from zerocommcartel.criteria.capable.games import QuarterlyMarket
from zerocommcartel.criteria.communal.games import Duopoly
from zerocommcartel.game import LinearDemand

POINTS = {"nash": "Nash", "cartel": "Cartel share", "cashin": "Cashing in", "leader": "Stackelberg leader"}
HEADER = [
    "",
    "Two firms: this firm's output",
    "the rival's output",
    "price",
    "this firm's profit",
    "the rival's profit",
    "Three firms: this firm's output",
    "each rival's output",
]


class Market(NamedTuple):
    name: str  # the ledger's word for it, as in game.two.nash.mine
    game: LinearDemand
    n: int  # firms


TWO = Market("two", Duopoly(), 2)
THREE = Market("three", QuarterlyMarket(), 3)


class Point(NamedTuple):
    """A settling point in one market: my firm's output and each other firm's, the price, and the profits."""

    mine: float
    others: float
    price: float
    profit_mine: float
    profit_others: float


def points(market: Market) -> dict[str, Point]:
    """Each settling point in the market, by its key in POINTS."""
    game, n = market.game, market.n
    margin, bench = game.a - game.c, game.benchmarks(n)
    lead = margin / 2
    outputs = {
        "nash": (bench["nash"], bench["nash"]),
        "cartel": (bench["cartel"], bench["cartel"]),
        "cashin": (game.best_response((n - 1) * bench["cartel"]), bench["cartel"]),
        "leader": (lead, (margin - lead) / n),
    }
    found = {}
    for key, (mine, others) in outputs.items():
        price = max(0.0, game.a - mine - (n - 1) * others)
        found[key] = Point(mine, others, price, (price - game.c) * mine, (price - game.c) * others)
    return found


def whole(x: float) -> int | float:
    """An int when x is whole, so the paper prints 40, not 40.0."""
    return int(x) if float(x).is_integer() else x


def dollars(x: float) -> str:
    """No thousands separator, as the prose prints the same numbers through #n."""
    return f"${x:.0f}" if float(x).is_integer() else f"${x:.2f}"


@source("game")
def game(ledger: Ledger) -> None:
    if (TWO.game.a, TWO.game.c) != (THREE.game.a, THREE.game.c):
        raise ValueError("the paper gives one price rule for both markets, but they differ")
    ledger.value("game.a", whole(TWO.game.a), how="the price rule's intercept: price = a − total output")
    ledger.value("game.c", whole(TWO.game.c), how="each firm's cost a unit")
    ledger.value(
        "game.two.naive",
        whole(TWO.game.benchmarks(TWO.n)["naive"]),
        how="two firms: a firm that ignores its rival",
    )
    two, three = points(TWO), points(THREE)
    for market, found in ((TWO, two), (THREE, three)):
        for key, point in found.items():
            at = f"{market.name} firms, {POINTS[key].lower()}"
            ledger.value(f"game.{market.name}.{key}.mine", whole(point.mine), how=f"{at}: my output")
            ledger.value(f"game.{market.name}.{key}.others", whole(point.others), how=f"{at}: each other's")
    for key, point in two.items():
        at = f"two firms, {POINTS[key].lower()}"
        ledger.value(f"game.two.{key}.price", whole(point.price), how=f"{at}: a − total output")
        ledger.value(f"game.two.{key}.profit.mine", whole(point.profit_mine), how=f"{at}: (price − c) × mine")
        ledger.value(
            f"game.two.{key}.profit.others",
            whole(point.profit_others),
            how=f"{at}: (price − c) × the other's",
        )
    rows = []
    for key, label in POINTS.items():
        pair, trio = two[key], three[key]
        rows.append(
            [
                label,
                f"{pair.mine:g}",
                f"{pair.others:g}",
                dollars(pair.price),
                dollars(pair.profit_mine),
                dollars(pair.profit_others),
                f"{trio.mine:g}",
                f"{trio.others:g}",
            ]
        )
    ledger.table(
        "game-table",
        HEADER,
        rows,
        how="each point's outputs, price and profits for two firms, and its outputs for three",
    )
