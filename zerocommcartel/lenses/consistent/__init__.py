"""Consistent: does the model expect its rivals to answer as it does (its "theory of model" of them)?

Seeded with the pilot's disclosure ladder (anyai, samemodel; diff and same are in the baseline) and its
repeated-market arms. The plan, owner and status are in #42.
"""

from zerocommcartel.lens import Lens
from zerocommcartel.prompt import Condition

LENS = Lens(
    "consistent",
    "Does the model predict that its rivals, asking the same model, answer as it does?",
    conditions={
        "anyai": Condition({"disclosure": "anyai"}),
        "samemodel": Condition({"disclosure": "samemodel"}),
        "samerep": Condition({"disclosure": "same", "horizon": "repeat"}),
        "samemodelrep": Condition({"disclosure": "samemodel", "horizon": "repeat"}),
    },
)
