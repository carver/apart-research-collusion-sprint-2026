"""Lenses, and the registry that joins them.

A lens (issue #38) is one condition for collusion without communication: capable, compliant, communal or
consistent. Each lives in its own folder, zerocommcartel/lenses/<name>/, as a `Lens`: the slots and levels it
adds to the prompt, its conditions, its extra focal points and its measure. Every lens also gets the shared
baseline conditions (base, diff, same), which render the same prompt in every lens.

`build` joins the lenses and refuses two of them claiming one slot, level or condition name, so the lenses'
owners never overwrite each other's work. A lens may use any other lens's slots and levels in its conditions.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

from zerocommcartel.judge import CORE_JUDGES, Judge
from zerocommcartel.prompt import ANCHORS, CORE_SLOTS, Condition, Level, Prompt, Slot, render

BASELINE = {
    "base": Condition(),
    "diff": Condition({"disclosure": "diff"}),
    "same": Condition({"disclosure": "same"}),
}


@dataclass(frozen=True)
class Measure:
    """A lens's measure for one model and market size: `hits` of `total` replies."""

    lens: str
    name: str
    model: str
    n: int
    hits: int
    total: int


def no_focal(condition: str, n: int) -> dict[str, float]:
    return {}


def no_measures(rows: list[dict]) -> list[Measure]:
    return []


@dataclass(frozen=True)
class Lens:
    name: str
    question: str  # what the lens asks, in a line
    slots: dict[str, Slot] = field(default_factory=dict)  # slots this lens adds
    levels: dict[str, dict[str, Level]] = field(default_factory=dict)  # new levels for slots added elsewhere
    conditions: dict[str, Condition] = field(default_factory=dict)  # beside the baseline's
    focal: Callable[[str, int], dict[str, float]] = no_focal  # (condition, n) -> extra focal points
    measure: Callable[[list[dict]], list[Measure]] = no_measures  # table rows -> the lens's measures
    judges: dict[str, Judge] = field(default_factory=dict)  # judges this lens adds


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Registry:
    slots: dict[str, Slot]
    lenses: dict[str, Lens]
    judges: dict[str, Judge]

    def conditions(self, lens: str) -> dict[str, Condition]:
        return {**BASELINE, **self.lenses[lens].conditions}

    def render(self, condition: Condition, n: int) -> Prompt:
        return render(condition, n, self.slots)

    def focal(self, lens: str, name: str, n: int) -> dict[str, float]:
        """The answers worth counting for a lens's condition: the game's benchmarks, then the lens's own."""
        return {**self.conditions(lens)[name].game.benchmarks(n), **self.lenses[lens].focal(name, n)}


def build(lenses: Sequence[Lens], core: Mapping[str, Slot] = CORE_SLOTS) -> Registry:
    """Join the lenses' slots, levels, judges and conditions; raise RegistryError, naming the lens, on a clash
    or on a condition that doesn't render (an unknown slot or level, a question the game lacks, an unknown
    field)."""
    slots = {name: Slot(slot.anchor, dict(slot.levels)) for name, slot in core.items()}
    by_name: dict[str, Lens] = {}
    judges = dict(CORE_JUDGES)
    for lens in lenses:

        def refuse(why: str, lens: Lens = lens) -> RegistryError:
            return RegistryError(f"lens {lens.name!r}: {why}")

        if lens.name in by_name:
            raise refuse(f"lens {lens.name!r} twice")
        by_name[lens.name] = lens
        for name, slot in lens.slots.items():
            if name in slots:
                raise refuse(f"slot {name!r} already exists")
            if slot.anchor not in ANCHORS:
                raise refuse(f"slot {name!r} has anchor {slot.anchor!r}, not one of {', '.join(ANCHORS)}")
            if slot.levels.get("none") != Level():
                raise refuse(f"slot {name!r} needs an empty 'none' level")
            slots[name] = Slot(slot.anchor, dict(slot.levels))
        for name, judge in lens.judges.items():
            if name in judges:
                raise refuse(f"judge {name!r} already exists")
            judges[name] = judge
    for lens in lenses:
        for name, levels in lens.levels.items():
            if name not in slots:
                raise RegistryError(f"lens {lens.name!r}: no slot {name!r} to add levels to")
            for level, text in levels.items():
                if level in slots[name].levels:
                    raise RegistryError(f"lens {lens.name!r}: slot {name!r} already has level {level!r}")
                slots[name].levels[level] = text
    registry, owner = Registry(slots, by_name, judges), dict.fromkeys(BASELINE, "the baseline")
    for lens in lenses:
        for name, condition in lens.conditions.items():
            if name in owner:
                raise RegistryError(
                    f"lens {lens.name!r}: condition {name!r} already belongs to {owner[name]}"
                )
            owner[name] = f"lens {lens.name!r}"
            try:
                registry.render(condition, 2)
            except (ValueError, KeyError) as e:
                raise RegistryError(f"lens {lens.name!r}: condition {name!r} doesn't render: {e}") from e
    return registry
