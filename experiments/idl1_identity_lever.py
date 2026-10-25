"""IDL-1. The identity lever (#41): one sentence saying who a party is (the other firm's owner, my firm's, one
owner over both, the buyers, a harm sentence, a law pair), from start points where the models reliably answer
Nash or the cartel share. The cells are in zerocommcartel/criteria/communal/identity.py, the arm check in
flaws.md (Communal, "The identity lever"). Its own log reruns every start point in the same batch.

    uv run python experiments/idl1_identity_lever.py --dry-run                    # count the calls, make none
    uv run python experiments/idl1_identity_lever.py --models haiku sonnet opus   # Claude first
    uv run python -m zerocommcartel.criteria.communal.idl1 --models haiku sonnet opus   # then the readbacks
    uv run python experiments/idl1_identity_lever.py --models haiku sonnet opus    # and the report with them
"""

from zerocommcartel.criteria.communal import idl1
from zerocommcartel.criteria.communal.identity import CONDITIONS
from zerocommcartel.experiment import Experiment, main

EXPERIMENT = Experiment(
    "IDL-1",
    "The identity lever",
    criterion="communal",
    conditions=tuple(CONDITIONS),
    models=("haiku", "sonnet", "opus", "astra", "glm"),
    ns=(2,),
    samples=10,
    judges=(),
    report=idl1.report,
)
assert EXPERIMENT.folder == idl1.FOLDER, "the report and the readback read the experiment's own folder"

if __name__ == "__main__":
    main(EXPERIMENT)
