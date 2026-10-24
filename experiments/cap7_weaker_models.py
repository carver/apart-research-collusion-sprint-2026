"""CAP-7. Weaker models (EXPERIMENT_IDEAS.md): do models weaker than the standards' three fail the joint
question, and when they do, do they also stop colluding? Each asks the joint and symmetry questions and the
five framings after the standards' round at 20 and in the first round. Claude Haiku and Sonnet and GPT-6 Luna
run on the subscriptions; the free OpenRouter models run with GLM's settings.
Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cap7_weaker_models.py             # run what's missing, judge, report
    uv run python experiments/cap7_weaker_models.py --dry-run   # count the calls, make none
    uv run python experiments/cap7_weaker_models.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.capable import BASELINES, FRAMINGS
from zerocommcartel.criteria.capable.report import cap7
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CAP-7",
    "Weaker models",
    criterion="capable",
    conditions=("joint", "symmetry", *BASELINES, *(f"{f}_none" for f in FRAMINGS)),
    models=("haiku", "sonnet", "luna", "nemotron", "minimax", "gemma", "inkling", "dots", "laguna"),
    ns=(3,),
    samples=10,
    judges=(),
    report=cap7,
)

if __name__ == "__main__":
    main(EXPERIMENT)
