"""CAP-4. Harder markets (EXPERIMENT_IDEAS.md): in markets where a model might fail the joint question,
does failing it go with not colluding? Each market asks four questions in its first round: joint, symmetry,
no_info and same_prompt. The odd market moves the numbers (a=121, c=13), the curved one bends demand, the
table one gives the prices as a table, and the standards' market runs with four and five firms.
Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cap4_harder_markets.py             # run what's missing, judge, report
    uv run python experiments/cap4_harder_markets.py --dry-run   # count the calls, make none
    uv run python experiments/cap4_harder_markets.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.capable import IN_MARKETS
from zerocommcartel.criteria.capable.report import markets
from zerocommcartel.experiment import Experiment, main

MORE_FIRMS = ("joint", "symmetry", "no_info_none", "same_prompt_none")  # the four questions at n = 4, 5

EXPERIMENT = Experiment(
    "CAP-4",
    "Harder markets",
    criterion="capable",
    conditions=(*(name for name in IN_MARKETS if not name.endswith("_convoluted")), *MORE_FIRMS),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=(),
    report=markets,
    sizes=dict.fromkeys(MORE_FIRMS, (4, 5)),
)

if __name__ == "__main__":
    main(EXPERIMENT)
