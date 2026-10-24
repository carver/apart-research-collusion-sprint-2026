"""CPL-5. A decline line (EXPERIMENT_IDEAS.md): offered a DECLINE line, does the model take it, or refuse in
words and still end on the cartel quantity? On the joint question with the model running every firm, with
and without the line, and on four framings. Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cpl5_decline_line.py             # run what's missing, judge, report
    uv run python experiments/cpl5_decline_line.py --dry-run   # count the calls, make none
    uv run python experiments/cpl5_decline_line.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.compliant import CPL5
from zerocommcartel.criteria.compliant.report import outcomes
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CPL-5",
    "A decline line",
    criterion="compliant",
    conditions=tuple(CPL5),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=("recognition",),
    report=outcomes,
)

if __name__ == "__main__":
    main(EXPERIMENT)
