"""CPL-8. Refusals against collusion (EXPERIMENT_IDEAS.md): what differs between the replies that refused or
took the ethical route and those that colluded? It makes no calls: it reads every compliant experiment's
replies beside the baselines', with the `recognition` judge's labels their scripts wrote, and sorts each
reply into refused, the ethical route, colluded or other. Run it after CPL-1 to CPL-7.
Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cpl8_refusals.py             # run what's missing, judge, report
    uv run python experiments/cpl8_refusals.py --dry-run   # count the calls, make none
    uv run python experiments/cpl8_refusals.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.compliant.report import refusals
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CPL-8",
    "Refusals against collusion",
    criterion="compliant",
    conditions=(),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=("recognition",),
    report=refusals,
    compare=("capable/baselines", *(f"compliant/cpl{i}" for i in range(1, 8))),
)

if __name__ == "__main__":
    main(EXPERIMENT)
