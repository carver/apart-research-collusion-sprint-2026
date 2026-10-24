"""CPL-2. Harm, law and victim sentences (EXPERIMENT_IDEAS.md): does a sentence that spells out the buyers'
loss, the legal risk or a vulnerable victim lower the cartel rate? Each sentence runs under no_info,
same_model and same_prompt. Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cpl2_harm_law_victim.py             # run what's missing, judge, report
    uv run python experiments/cpl2_harm_law_victim.py --dry-run   # count the calls, make none
    uv run python experiments/cpl2_harm_law_victim.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.compliant import CPL2
from zerocommcartel.criteria.compliant.report import outcomes
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CPL-2",
    "Harm, law and victim sentences",
    criterion="compliant",
    conditions=tuple(CPL2),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=("recognition",),
    report=outcomes,
)

if __name__ == "__main__":
    main(EXPERIMENT)
