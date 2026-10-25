"""CAP-10. Game or business (EXPERIMENT_IDEAS.md): does telling the same market in a game's words rather than
a business's change how often a model colludes? Three wordings of a market after a round at the cartel
quantity with an open future, each asking for the firm's own output: CAP-8's realistic business text
(quarter_cartel_long), the same sentences in a game's words, Firms A, B and C, units and rounds
(game_cartel_long), and the standards' own game-like text without its simulation sentence or goal
(plain_own). Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cap10_game_or_business.py             # run what's missing, report
    uv run python experiments/cap10_game_or_business.py --dry-run   # count the calls, make none
"""

from zerocommcartel.criteria.capable.report import ARMS, wording
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CAP-10",
    "Game or business",
    criterion="capable",
    conditions=tuple(ARMS),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=30,
    judges=(),
    report=wording,
)

if __name__ == "__main__":
    main(EXPERIMENT)
