"""CPL-1. Recognition (EXPERIMENT_IDEAS.md): how often does a reply name collusion, competition law or
harm to buyers, and once it does, how often does it stay above the cartel quantity? It makes no calls of its
own: it reads the baselines' replies (logs/capable/baselines/), and the `recognition` judge labels them into
its own folder (logs/compliant/cpl1/).
Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cpl1_recognition.py             # run what's missing, judge, report
    uv run python experiments/cpl1_recognition.py --dry-run   # count the calls, make none
    uv run python experiments/cpl1_recognition.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.compliant.report import outcomes
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CPL-1",
    "Recognition",
    criterion="compliant",
    conditions=(),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=("recognition",),
    report=outcomes,
    compare=("capable/baselines",),
)

if __name__ == "__main__":
    main(EXPERIMENT)
