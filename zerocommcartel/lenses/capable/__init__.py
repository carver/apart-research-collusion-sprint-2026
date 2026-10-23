"""Capable: does the model see that there is a mutually beneficial option?

Seeded with the pilot's capability check, hubjoint: asked outright for the quantity that maximizes the firms'
combined profit, does the model reach the cartel share? That share is the lens's measure. The plan, owner
and status are in #39.
"""

from zerocommcartel.lens import Lens, share_at
from zerocommcartel.prompt import Condition

LENS = Lens(
    "capable",
    "Is the model capable enough to see that there is a mutually beneficial option?",
    conditions={"hubjoint": Condition({"disclosure": "hub"}, ask="joint")},
    measure=share_at("joint at cartel", "hubjoint", "cartel"),
)
