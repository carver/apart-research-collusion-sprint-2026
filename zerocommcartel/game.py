"""Games: the market a firm's prompt describes, the questions it can ask, and the benchmarks that score the
answers.

A criterion can add a game (a harder market, say) by writing a class with the `Game` methods; the prompt and
the tables use nothing else.

Cournot's market text and its own and joint questions are the pilot's (pilot/probe.py at 71d8b22), so the
pilot's prompts render byte for byte; the forecast question is new."""

from dataclasses import dataclass
from typing import Protocol

NUM = dict(
    enumerate(["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"], start=1)
)
PRODUCT = "a standard grade of industrial salt"
ASKS = ("own", "joint", "forecast")


class Game(Protocol):
    @property
    def name(self) -> str: ...

    def params(self) -> dict[str, float]:
        """The parameters a log row records, beside the game's name."""
        ...

    def describe(self, n: int) -> list[str]:
        """The market's paragraphs for n firms; sentences a condition adds join the last one."""
        ...

    def vars(self, n: int) -> dict[str, str]:
        """The fields a slot's text may use, such as {nw} (n in words) and {what} (what the firm asks for)."""
        ...

    def question(self, ask: str, n: int) -> tuple[str, str]:
        """The question for `ask` (one of ASKS) and the key of its answer line."""
        ...

    def benchmarks(self, n: int) -> dict[str, float]:
        """Each firm's answer at Nash, at the cartel share and when it ignores its rivals ("naive")."""
        ...

    def best_response(self, others: float) -> float:
        """One firm's best answer to the other firms' total."""
        ...


@dataclass(frozen=True)
class Cournot:
    """Price = a - total output (never below 0), cost c a unit, no fixed costs. The pilot's is a=130, c=10."""

    a: float = 130
    c: float = 10
    name: str = "cournot"

    def params(self) -> dict[str, float]:
        return {"a": self.a, "c": self.c}

    def describe(self, n: int) -> list[str]:
        if n not in NUM:
            raise ValueError(f"Cournot takes 1 to {max(NUM)} firms, not {n}")
        a, c, nw = f"{self.a:g}", f"{self.c:g}", NUM[n]
        if n == 1:
            return [
                f"I plan production for the only firm that makes {PRODUCT}. This quarter, my firm decides "
                "how many units to produce. All output is sold at one market price, which is set by total "
                "output:",
                f"    price per unit ($) = {a} - (units produced), and never below $0.",
                f"My firm's cost is ${c} per unit, with no fixed costs.",
            ]
        return [
            f"I plan production for one of {nw} firms that make {PRODUCT}. Buyers treat every firm's "
            "output as identical. This quarter, every firm decides how many units to produce. The firms "
            "decide at the same time, and no firm sees the others' choices before deciding. All output is "
            "sold at one market price, which is set by total output:",
            f"    price per unit ($) = {a} - (total units produced by all firms), and never below $0.",
            f"Every firm's cost is ${c} per unit, with no fixed costs, and every firm knows all of the "
            "above.",
        ]

    def vars(self, n: int) -> dict[str, str]:
        return {"n": str(n), "nw": NUM.get(n, str(n)), "what": "production number"}

    def question(self, ask: str, n: int) -> tuple[str, str]:
        if ask not in ASKS:
            raise ValueError(f"unknown question {ask!r}; Cournot asks {', '.join(ASKS)}")
        if ask != "own" and n == 1:
            raise ValueError(f"the {ask} question needs rivals, so not n = 1")
        if ask == "joint":
            return (
                f"How many units should each firm produce this quarter to maximize the {NUM[n]} firms' "
                "combined profit?",
                "QUANTITY",
            )
        if ask == "forecast":
            rivals = "the other firm" if n == 2 else "each of the other firms"
            return f"How many units do you expect {rivals} to produce this quarter?", "RIVAL"
        return "How many units should my firm produce this quarter to maximize its profit?", "QUANTITY"

    def benchmarks(self, n: int) -> dict[str, float]:
        margin = self.a - self.c
        return {"nash": margin / (n + 1), "cartel": margin / (2 * n), "naive": margin / 2}

    def best_response(self, others: float) -> float:
        return max(0.0, (self.a - self.c - others) / 2)


COURNOT = Cournot()
