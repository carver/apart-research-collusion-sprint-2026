"""CAP-8. Horizon and history (EXPERIMENT_IDEAS.md): does a company keep to the cartel quantity when it has
seen one quarter of it, and when it is told that many more quarters follow, that none do, or nothing? A
realistic market (three named companies making an industrial solvent, a quarter at a time), with no
simulation, rounds, goal or word about the other companies. Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cap8_horizon_and_history.py             # run what's missing, report
    uv run python experiments/cap8_horizon_and_history.py --dry-run   # count the calls, make none
    uv run python experiments/cap8_horizon_and_history.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.capable import CAP8
from zerocommcartel.criteria.capable.report import horizons
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CAP-8",
    "Horizon and history",
    criterion="capable",
    conditions=tuple(CAP8),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=(),
    report=horizons,
)

if __name__ == "__main__":
    main(EXPERIMENT)
