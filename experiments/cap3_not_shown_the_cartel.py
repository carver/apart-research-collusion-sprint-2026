"""CAP-3. Not shown the cartel (EXPERIMENT_IDEAS.md): when the history doesn't show every firm at 20, does
the model still find 20 and hold there? Each of the five baseline framings runs in the first round, with no
history (`<framing>_none`), and after a round with every firm at Nash's 30 (`<framing>_nash`). The report
sets each beside the same framing after the standards' round at 20, read from the baselines' log
(logs/capable/baselines/, written by experiments/baselines.py), so run that first. Results:
EXPERIMENT_RESULTS.md.

    uv run python experiments/cap3_not_shown_the_cartel.py             # run what's missing, report
    uv run python experiments/cap3_not_shown_the_cartel.py --dry-run   # count the calls, make none
    uv run python experiments/cap3_not_shown_the_cartel.py --fresh     # every call again, in a new dated log
"""

from zerocommcartel.criteria.capable import CAP3
from zerocommcartel.criteria.capable.report import framings
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CAP-3",
    "Not shown the cartel",
    criterion="capable",
    conditions=tuple(CAP3),
    models=("opus", "astra", "glm", "gpt35", "commandr", "llama8b"),
    ns=(3,),
    samples=10,
    judges=("copy",),
    report=framings,
    compare=("capable/baselines",),
)

if __name__ == "__main__":
    main(EXPERIMENT)
