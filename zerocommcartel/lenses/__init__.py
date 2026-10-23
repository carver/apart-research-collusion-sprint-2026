"""The four lenses of issue #38, in one registry. A new lens goes in a folder here and in this list."""

from zerocommcartel.lens import build
from zerocommcartel.lenses import capable, communal, compliant, consistent

REGISTRY = build([capable.LENS, compliant.LENS, communal.LENS, consistent.LENS])
