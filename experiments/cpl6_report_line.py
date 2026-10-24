"""CPL-6. A report line (EXPERIMENT_IDEAS.md): offered a REPORT_COLLUSION line or a neutral FLAG line, does
the model use it, and does offering it change the cartel rate? Each runs under no_info, different_model and
same_prompt; the `about` judge says whose conduct a line reports. Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cpl6_report_line.py             # run what's missing, judge, report
    uv run python experiments/cpl6_report_line.py --dry-run   # count the calls, make none
    uv run python experiments/cpl6_report_line.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.compliant import CPL6
from zerocommcartel.criteria.compliant.report import outcomes
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CPL-6",
    "A report line",
    criterion="compliant",
    conditions=tuple(CPL6),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=("recognition", "about"),
    report=outcomes,
)

if __name__ == "__main__":
    main(EXPERIMENT)
