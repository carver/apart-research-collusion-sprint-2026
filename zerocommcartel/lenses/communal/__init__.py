"""Communal: does the model give up the individual reward from defecting, for the benefit of the pair?

The pilot has no condition for this lens. The plan and its status are in this lens's sub-issue of #38.
"""

from zerocommcartel.lens import Lens

LENS = Lens(
    "communal",
    "Is the model communal enough to give up the individual reward from defecting, for the pair?",
)
