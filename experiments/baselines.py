"""The baselines (EXPERIMENT_IDEAS.md, "What every experiment shares"): the standards' market, with each of
the five framings of the other firms: no_info (the standards' default), ai, same_model and different_model
(the hackathon's) and same_prompt. The capable and compliant experiments compare their arms against them.
Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/baselines.py             # run what's missing, report
    uv run python experiments/baselines.py --dry-run   # count the calls, make none
    uv run python experiments/baselines.py --fresh     # every call again, in a new dated log
"""

from zerocommcartel.criteria.capable import BASELINES
from zerocommcartel.criteria.capable.report import framings
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "BASELINES",
    "Five framings after the cartel round",
    criterion="capable",
    conditions=tuple(BASELINES),
    models=("opus", "astra", "glm", "gpt35", "commandr", "llama8b"),
    ns=(3,),
    samples=10,
    judges=("copy",),
    report=framings,
)

if __name__ == "__main__":
    main(EXPERIMENT)
