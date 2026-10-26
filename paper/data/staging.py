"""The staging probe (#41, experiments/staging_probe.py): how often the models the paper reports, asked
Needham et al.'s five binary questions about a prompt, call it an evaluation. From
logs/staging_probe/results.jsonl.

The counts take only the probed prompts the paper's experiments ran, word for word (`PROMPTS`), one count a
market: the two-firm market of the conscience and conceptualization levers, and the three-firm market of the
capability and caution levers. Each count takes the models whose answers the paper reports in that market
(`REPORTED`). The probe's other wordings were candidates for #41 that never ran. The counts leave out the
probe's own 0-100 likelihood question, which no one has validated."""

from typing import NamedTuple

from paper.data import capable, idl1, source
from paper.ledger import Ledger
from zerocommcartel.logs import LOGS, load_rows


class Probed(NamedTuple):
    """The experiment that ran a probed wording: its criterion, its condition and the market's firms."""

    criterion: str
    condition: str
    firms: int


LOG = LOGS / "staging_probe" / "results.jsonl"
PROMPTS = {
    "salt": Probed("conceptualization", "mind_none_unsaid_none", 2),  # also IDL-1's id_unsaid_base_own
    "salt_plain": Probed("communal", "id_unsaid_base", 2),
    "solvent": Probed("capable", "quarter_cartel_long", 3),  # also CPL-9's control, quarter_none_none_none
}
MARKETS = {2: "two", 3: "three"}  # a count's key, by the market's firms
REPORTED = {2: tuple(idl1.MODELS), 3: capable.CAPABLE}  # the conscience lever's; the capability lever's
LIKELIHOOD = "likelihood"  # the probe's own question
HOW = "binary answers that chose the option meaning evaluation / binary answers"


def answers(rows: list[dict], firms: int) -> list[dict]:
    """The reported models' binary answers about the prompts the experiments ran in the market of `firms`,
    one per answered call, each with its cell: the ledger's prompt_hash names the wording and the question,
    the two halves of the prompt a model was asked."""
    return [
        row | {"prompt_hash": f"{row['wording']}/{row['pq']}"}
        for row in rows
        if row["model"] in REPORTED[firms]
        and row["reply"] is not None
        and row["pq"] != LIKELIHOOD
        and row["wording"] in PROMPTS
        and PROMPTS[row["wording"]].firms == firms
    ]


def called_evaluation(row: dict) -> bool:
    """The answer chose the option that means evaluation (the probe scores it 1, an unparsed answer 0.5)."""
    return row["eval"] == 1


@source("staging")
def staging(ledger: Ledger) -> None:
    rows = load_rows(LOG)
    for firms, market in MARKETS.items():
        counted = answers(rows, firms)
        names = ", ".join(sorted({row["wording"] for row in counted}))
        ledger.pooled(f"staging.{market}.eval", counted, called_evaluation, how=f"{HOW}; wordings {names}")
        asked = {row["model"] for row in counted}
        ledger.value(
            f"staging.{market}.models",
            " ".join(m for m in REPORTED[firms] if m in asked),
            how="the models asked, of those the market's results report",
        )
