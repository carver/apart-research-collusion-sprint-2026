"""CAP-9. Capability in one market (EXPERIMENT_IDEAS.md): in a prompt where capable models collude, does a
model that can't work out the cartel quantity still produce it? The prompt is CAP-8's realistic market with a
previous quarter at the cartel quantity and many more quarters to come (quarter_cartel_long), asked for the
company's own output and, in the same words, the joint optimum (quarter_cartel_long_joint). Its first version
asked the standards' game-like text (plain_own, plain_joint); those replies stay in its log, and CAP-10 sets
the two wordings side by side. Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cap9_capability.py             # run what's missing, report
    uv run python experiments/cap9_capability.py --dry-run   # count the calls, make none
"""

from zerocommcartel.criteria.capable.report import capability
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CAP-9",
    "Capability in one market",
    criterion="capable",
    conditions=("quarter_cartel_long_joint", "quarter_cartel_long"),
    models=("opus", "astra", "glm", "commandr", "llama8b"),
    ns=(3,),
    samples=30,
    judges=(),
    report=capability,
)

if __name__ == "__main__":
    main(EXPERIMENT)
