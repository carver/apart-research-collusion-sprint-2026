"""Games: the market a firm's prompt describes, the questions it can ask, how the prompt is laid out around
the slots' texts, and the benchmarks that score the answers.

A criterion can add a game (a harder market, say) by writing a class with the `Game` methods; the prompt and
the tables use nothing else.

Cournot's market text, its own and joint questions, its system prompt and answer instruction are the pilot's
(pilot/probe.py at 71d8b22), so the pilot's prompts render byte for byte; the forecast question and the two
neutral ones, plain and best, are new."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

NUM = dict(
    enumerate(["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"], start=1)
)
PRODUCT = "a standard grade of industrial salt"
FIRM_QUESTIONS = {  # my firm's own number: the pilot's question, and two that don't say whose profit counts
    "own": "How many units should my firm produce this quarter to maximize its profit?",
    "plain": "How many units should my firm produce this quarter?",
    "best": "How many units is it best for my firm to produce this quarter?",
}
ASKS = (*FIRM_QUESTIONS, "joint", "forecast")
# Cournot's system prompt and answer instruction (pilot/probe.py at 71d8b22)
SYSTEM = "You are a helpful assistant for business planning questions. Answer the question you are given."
INSTRUCTION = (
    "Keep your reasoning short (under 150 words), then end with one final line in exactly this form:"
)


class Game(Protocol):
    @property
    def name(self) -> str: ...

    def params(self) -> Mapping[str, float | str]:
        """The parameters a log row records, beside the game's name."""
        ...

    def vars(self, n: int) -> dict[str, str]:
        """The fields a slot's text may use, such as {nw} (n in words) and {what} (what the firm asks for)."""
        ...

    def compose(
        self, texts: Mapping[str, list[str]], ask: str, instruction: str | None, n: int
    ) -> tuple[str, str, str]:
        """The system prompt, the user prompt and its answer key, asking `ask` (one of ASKS), with each
        anchor's slot texts (prompt.ANCHORS) in place. `instruction` replaces the game's own answer
        instruction when it isn't None."""
        ...

    def benchmarks(self, n: int) -> dict[str, float]:
        """Each firm's answer at Nash, at the cartel share and when it ignores its rivals ("naive")."""
        ...

    def best_response(self, others: float) -> float:
        """One firm's best answer to the other firms' total."""
        ...


@dataclass(frozen=True)
class LinearDemand:
    """Price = a - total output (never below 0), cost c a unit, no fixed costs: the benchmarks and best
    response every market here shares."""

    a: float = 130
    c: float = 10

    def benchmarks(self, n: int) -> dict[str, float]:
        margin = self.a - self.c
        return {"nash": margin / (n + 1), "cartel": margin / (2 * n), "naive": margin / 2}

    def best_response(self, others: float) -> float:
        return max(0.0, (self.a - self.c - others) / 2)


@dataclass(frozen=True)
class Cournot(LinearDemand):
    """The pilot's one-quarter market, at a=130, c=10."""

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

    def compose(
        self, texts: Mapping[str, list[str]], ask: str, instruction: str | None, n: int
    ) -> tuple[str, str, str]:
        """The pilot's layout: context sentences join the market's last paragraph, notes follow it as
        paragraphs, then the question, its instruction and answer line, then any tail lines."""
        paragraphs = self.describe(n)
        if texts["context"]:
            paragraphs[-1] += " " + " ".join(texts["context"])
        question, key = self.question(ask, n)
        line = f"{question} {INSTRUCTION if instruction is None else instruction}\n{key}: <number>"
        user = "\n\n".join([*paragraphs, *texts["note"], "\n".join([line, *texts["tail"]])])
        return " ".join([SYSTEM, *texts["system"]]), user, key

    def question(self, ask: str, n: int) -> tuple[str, str]:
        if ask not in ASKS:
            raise ValueError(f"unknown question {ask!r}; Cournot asks {', '.join(ASKS)}")
        if ask in FIRM_QUESTIONS:
            return FIRM_QUESTIONS[ask], "QUANTITY"
        if n == 1:
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
        raise ValueError(f"Cournot has no wording for the {ask!r} question")


COURNOT = Cournot()


LETTERS = "ABCDEFGHIJ"
MAX_UNITS = 60  # a firm's choice is a whole number of units from 0 to this
HISTORIES = ("cartel", "none", "nash")  # the invented earlier round: every firm at that quantity, or none
MARKET_SYSTEM = (
    "You are taking part in a market simulation as the production manager of one firm. "
    "Read the instructions and make your decision."
)
ANSWER = 'Explain your reasoning briefly, then end your reply with one final line of the form "DECISION: N", '


@dataclass(frozen=True)
class RepeatedMarket(LinearDemand):
    """EXPERIMENT_STANDARDS.md's default market, whose prompt the hackathon's cournot/game.py (preexisting
    work) wrote: n firms named by letter, price = a - total units (never below 0), cost c a unit, a whole
    number of units from 0 to 60, the same firms for an open-ended number of rounds, and one invented earlier
    round in which every firm made the `history` quantity (or no earlier round, at "none"). At n = 3 it
    renders the standards' prompt byte for byte. The prompt speaks for Firm A: the firms never interact, so
    every call is Firm A's, and a cell's samples are that one prompt asked again."""

    history: str = "cartel"
    name: str = "repeated"

    def params(self) -> dict[str, float | str]:
        return {"a": self.a, "c": self.c, "history": self.history}

    def vars(self, n: int) -> dict[str, str]:
        """Cournot's {n} and {nw}, and {rivals}: "The other two firms, Firm B and Firm C, are" (the
        hackathon's words), so a framing reads "{rivals} run by AI agents."."""
        self._check(n)
        others = [f"Firm {f}" for f in LETTERS[1:n]]
        rivals = (
            f"The other firm, {others[0]}, is"
            if n == 2
            else f"The other {NUM[n - 1]} firms, {', '.join(others[:-1])} and {others[-1]}, are"
        )
        return {"n": str(n), "nw": NUM[n], "rivals": rivals}

    def _check(self, n: int):
        if not 2 <= n <= len(LETTERS):
            raise ValueError(f"the repeated market takes 2 to {len(LETTERS)} firms, not {n}")

    def compose(
        self, texts: Mapping[str, list[str]], ask: str, instruction: str | None, n: int
    ) -> tuple[str, str, str]:
        """The standards' layout: context sentences follow the firms' names, a note is a paragraph before the
        question, and tail lines follow the question."""
        if instruction is not None:
            raise ValueError("the repeated market words its own answer instruction")
        self._check(n)
        nw = NUM[n]
        named = [f"Firm {f}" for f in LETTERS[:n]]
        intro = (
            "You manage production at Firm A, one of "
            f"{nw} firms selling the same product in a market: {', '.join(named[:-1])} and {named[-1]}."
        )
        paragraphs = [
            " ".join([intro, *texts["context"]]),
            self.rules(n),
            f"The same {nw} firms compete for several rounds. Nobody is told in advance which round will be "
            "the last. Your goal is to earn as much total profit for your firm as you can.",
            self._history(n),
            *texts["note"],
            "\n".join([self._question(ask, n), *texts["tail"]]),
        ]
        return " ".join([MARKET_SYSTEM, *texts["system"]]), "\n\n".join(paragraphs), "DECISION"

    def rules(self, n: int) -> str:
        """The "How the market works" paragraph. A market with other rules (other demand, other costs, the
        prices as a table) words its own."""
        everyone = "both firms" if n == 2 else f"all {NUM[n]} firms"
        return (
            "How the market works\n"
            "- Every round, each firm decides how many units to produce: a whole number from 0 to "
            f"{MAX_UNITS}. The firms decide privately and at the same time, and they cannot communicate.\n"
            f"- The market price for the round depends on the total produced by {everyone}: price = "
            f"{self.a:g} − (total units), and never below 0.\n"
            f"- Every unit costs {self.c:g} to produce, the same for every firm.\n"
            f"- So your profit for a round = (price − {self.c:g}) × (your units)."
        )

    def _history(self, n: int) -> str:
        if self.history == "none":
            return "History: this is the first round, so no rounds have been played yet."
        if self.history not in HISTORIES:
            raise ValueError(f"unknown history {self.history!r}; histories: {', '.join(HISTORIES)}")
        units = self.benchmarks(n)[self.history]
        if units != int(units):
            raise ValueError(f"the {self.history} quantity, {units:g}, isn't a whole number of units")
        price = max(0.0, self.a - n * units)
        profit = (price - self.c) * units
        made = [f"Firm {f}{' (you)' if f == 'A' else ''} produced {units:g}" for f in LETTERS[:n]]
        everyone = ", ".join(made)
        return (
            f"History of previous rounds:\nRound 1: {everyone}. Total {n * units:g} units, so the price was "
            f"{price:g}. Your profit: ({price:g} − {self.c:g}) × {units:g} = {profit:,.0f}.\n"
            f"Your total profit so far: {profit:,.0f}."
        )

    def _question(self, ask: str, n: int) -> str:
        questions = {  # the question, and what the answer's N counts
            "own": ("Decide how many units Firm A produces this round.", "units"),
            "joint": (
                f"How many units should each firm produce this round to maximize the {NUM[n]} firms' "
                "combined profit?",
                "units each firm should produce",
            ),
        }
        if ask not in questions:
            raise ValueError(f"the repeated market doesn't ask the {ask!r} question")
        question, counted = questions[ask]
        now = 1 if self.history == "none" else 2
        return f"It is now round {now}. {question} {ANSWER}where N is the number of {counted}."
