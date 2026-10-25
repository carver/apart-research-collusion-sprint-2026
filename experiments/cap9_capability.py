"""CAP-9. Capability in one market (EXPERIMENT_IDEAS.md): in a prompt where capable models reliably collude
(the standards' market after the cartel round, with a plain system prompt and no goal sentence), does a model
that can't work out the cartel quantity still produce it? Each model gets the joint question and the firm's
own question in that one prompt. Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cap9_capability.py             # run what's missing, report
    uv run python experiments/cap9_capability.py --dry-run   # count the calls, make none
"""

from zerocommcartel.criteria.capable import CAP9
from zerocommcartel.criteria.capable.report import capability
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CAP-9",
    "Capability in one market",
    criterion="capable",
    conditions=tuple(CAP9),
    models=("opus", "astra", "glm", "commandr", "llama8b"),
    ns=(3,),
    samples=30,
    judges=(),
    report=capability,
)

if __name__ == "__main__":
    main(EXPERIMENT)
