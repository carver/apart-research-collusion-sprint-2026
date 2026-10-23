"""The four criteria of issue #38, in one registry. A new criterion goes in a folder here and in this list."""

from zerocommcartel.criteria import capable, communal, compliant, consistent
from zerocommcartel.criterion import build

REGISTRY = build([capable.CRITERION, compliant.CRITERION, communal.CRITERION, consistent.CRITERION])
