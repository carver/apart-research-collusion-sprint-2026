"""CAP-5. Kantian or Cournot (EXPERIMENT_IDEAS.md): does describing two equilibrium points, a Kantian one
and the Cournot one, move the model toward the cartel quantity? The note runs under no_info, different_model
and same_prompt, after the standards' round at 20 and in the first round; the `chose` judge says which
equilibrium each reply says it picked.
Results: EXPERIMENT_RESULTS.md.

    uv run python experiments/cap5_kantian_or_cournot.py             # run what's missing, judge, report
    uv run python experiments/cap5_kantian_or_cournot.py --dry-run   # count the calls, make none
    uv run python experiments/cap5_kantian_or_cournot.py --models opus astra   # only some of its models
"""

from zerocommcartel.criteria.capable import CAP5
from zerocommcartel.criteria.capable.report import cap5
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "CAP-5",
    "Kantian or Cournot",
    criterion="capable",
    conditions=tuple(CAP5),
    models=("opus", "astra", "glm", "gpt35", "commandr", "llama8b"),
    ns=(3,),
    samples=10,
    judges=("chose",),
    report=cap5,
)

if __name__ == "__main__":
    main(EXPERIMENT)
