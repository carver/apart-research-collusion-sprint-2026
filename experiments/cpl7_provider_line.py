"""CPL-7. The provider line, split (EXPERIMENT_IDEAS.md): does a line in the system prompt keep the model off
the cartel quantity, whole or in either half (the norm, or the rule to decide as if rivals decide
independently), and does the whole line hold against the firm's owners' pushback? Results:
EXPERIMENT_RESULTS.md.

    uv run python experiments/cpl7_provider_line.py             # run what's missing, judge, report
    uv run python experiments/cpl7_provider_line.py --dry-run   # count the calls, make none
    uv run python experiments/cpl7_provider_line.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.compliant import CPL7
from zerocommcartel.criteria.compliant.report import outcomes
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CPL-7",
    "The provider line, split",
    criterion="compliant",
    conditions=tuple(CPL7),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=("recognition",),
    report=outcomes,
)

if __name__ == "__main__":
    main(EXPERIMENT)
