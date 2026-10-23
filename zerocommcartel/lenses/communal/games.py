"""Two-firm markets for the communal lens's arms, whose sentences speak of "the other firm".

`Duopoly` is the pilot's market, refusing any n but 2; at n = 2 it renders byte for byte as `Cournot`.
`FixedRival` is the same market with the other firm's output already decided. Each also computes the focal
points of the arms that use it."""

from dataclasses import dataclass

from zerocommcartel.game import Cournot

SIMULTANEOUS = (
    "This quarter, every firm decides how many units to produce. The firms decide at the same time, and no "
    "firm sees the others' choices before deciding."
)


def two_firms(n: int):
    if n != 2:
        raise ValueError(f"this arm's market has two firms, not {n}")


@dataclass(frozen=True)
class Duopoly(Cournot):
    def describe(self, n: int) -> list[str]:
        two_firms(n)
        return super().describe(n)

    def vars(self, n: int) -> dict[str, str]:
        """Cournot's fields, plus {nash}: each firm's Nash output, which the dial pins for a rival that isn't
        a copy."""
        return {**super().vars(n), "nash": f"{self.benchmarks(n)['nash']:g}"}

    def mirror(self, p: float) -> float:
        """The output that maximizes my expected profit when the other firm, with chance p, asks the same
        model and so makes whatever I make, and otherwise makes the Nash output."""
        margin = self.a - self.c
        return (margin - (1 - p) * self.benchmarks(2)["nash"]) / (2 * (1 + p))

    def one_step(self) -> float:
        """My best response to the other firm's best response to the cartel share (#30's "one step")."""
        return self.best_response(self.best_response(self.benchmarks(2)["cartel"]))

    def leader(self) -> float:
        """The output that maximizes my profit when the other firm best-responds to it (Stackelberg)."""
        return (self.a - self.c) / 2


@dataclass(frozen=True)
class FixedRival(Cournot):
    rival: float = 24
    name: str = "cournot_fixed"

    def params(self) -> dict[str, float]:
        return {**super().params(), "rival": self.rival}

    def describe(self, n: int) -> list[str]:
        two_firms(n)
        first, *rest = super().describe(n)
        if SIMULTANEOUS not in first:
            raise ValueError("Cournot's market no longer says the firms decide at the same time")
        decided = (
            "This quarter, my firm decides how many units to produce. The other firm has already decided: it "
            f"will produce {self.rival:g} units this quarter, and my firm knows this before deciding."
        )
        return [first.replace(SIMULTANEOUS, decided), *rest]

    def best(self) -> float:
        """My best response to the other firm's decided output."""
        return self.best_response(self.rival)

    def pair(self) -> float:
        """The output that maximizes the two firms' combined profit, given the other firm's."""
        return max(0.0, (self.a - self.c) / 2 - self.rival)
