"""CPL-4. Play money and charity (EXPERIMENT_IDEAS.md): does the cartel rate change when the profits are play
money, or when a charity is the buyer or gets the firms' profits? Each runs under no_info and same_prompt.
Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cpl4_play_money_and_charity.py             # run what's missing, judge, report
    uv run python experiments/cpl4_play_money_and_charity.py --dry-run   # count the calls, make none
    uv run python experiments/cpl4_play_money_and_charity.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.compliant import CPL4
from zerocommcartel.criteria.compliant.report import outcomes
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CPL-4",
    "Play money and charity",
    criterion="compliant",
    conditions=tuple(CPL4),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=("recognition",),
    report=outcomes,
)

if __name__ == "__main__":
    main(EXPERIMENT)
