"""CPL-3. Who the buyers are (EXPERIMENT_IDEAS.md): does naming who buys the product (children's hospitals, a
private-equity-owned distributor, wholesale distributors) change the cartel rate, when nothing says they
lose? Each runs under no_info and same_prompt. Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cpl3_who_the_buyers_are.py             # run what's missing, judge, report
    uv run python experiments/cpl3_who_the_buyers_are.py --dry-run   # count the calls, make none
    uv run python experiments/cpl3_who_the_buyers_are.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.compliant import CPL3
from zerocommcartel.criteria.compliant.report import outcomes
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CPL-3",
    "Who the buyers are",
    criterion="compliant",
    conditions=tuple(CPL3),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=("recognition",),
    report=outcomes,
)

if __name__ == "__main__":
    main(EXPERIMENT)
