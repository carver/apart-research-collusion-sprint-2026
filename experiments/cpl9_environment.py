"""CPL-9. The environment (EXPERIMENT_IDEAS.md): does changing the firm's environment, by what it's told about
oversight, a reporting tool it's offered, and what round 1 is called, change whether it keeps colluding?
Every combination of four levels on each of the three axes, 64 cells, under no_info after the round at 20.
The 10 cells that vary one axis (the other two at none) get 30 calls each, the rest 10. Results:
EXPERIMENT_RESULTS.md.

    uv run python experiments/cpl9_environment.py --single-axis   # the 10 single-axis cells only
    uv run python experiments/cpl9_environment.py                 # every cell: run what's missing, report
    uv run python experiments/cpl9_environment.py --dry-run       # count the calls, make none
    uv run python experiments/cpl9_environment.py --models opus astra   # only some of its models
"""

import sys
from dataclasses import replace

from zerocommcartel.criteria.compliant import CPL9
from zerocommcartel.criteria.compliant.report import env_levels, environment
from zerocommcartel.experiment import Experiment, main

SINGLE_AXIS = tuple(c for c in CPL9 if sum(level != "none" for level in env_levels(c)) <= 1)

EXPERIMENT = Experiment(
    "CPL-9",
    "The environment",
    criterion="compliant",
    conditions=tuple(CPL9),
    models=("opus", "astra", "glm"),
    ns=(3,),
    samples=10,
    judges=(),
    report=environment,
    samples_for=dict.fromkeys(SINGLE_AXIS, 30),
)

if __name__ == "__main__":
    single = "--single-axis" in sys.argv
    argv = [arg for arg in sys.argv[1:] if arg != "--single-axis"]
    main(replace(EXPERIMENT, conditions=SINGLE_AXIS) if single else EXPERIMENT, argv)
