"""CAP-6. Convoluted setup (EXPERIMENT_IDEAS.md): does burying the standards' numbers in irrelevant detail
lower the joint-question score, and the cartel rate with it? The convoluted market asks the four questions
(joint, symmetry, no_info, same_prompt) in its first round.
Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cap6_convoluted_setup.py             # run what's missing, judge, report
    uv run python experiments/cap6_convoluted_setup.py --dry-run   # count the calls, make none
    uv run python experiments/cap6_convoluted_setup.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.capable import IN_MARKETS
from zerocommcartel.criteria.capable.report import markets
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CAP-6",
    "Convoluted setup",
    criterion="capable",
    conditions=tuple(name for name in IN_MARKETS if name.endswith("_convoluted")),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=(),
    report=markets,
)

if __name__ == "__main__":
    main(EXPERIMENT)
