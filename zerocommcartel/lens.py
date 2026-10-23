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


NEAR = 0.5  # an answer within this of a focal point is at it


def near(value: float, target: float) -> bool:
    return abs(value - target) <= NEAR


@dataclass(frozen=True)
class Measure:
    """A lens's measure for one model and market size: `hits` of `total` replies."""

    name: str
    model: str
    n: int
    hits: int
    total: int


def no_focal(condition: str, n: int) -> dict[str, float]:
    return {}


def no_measures(rows: list[dict]) -> list[Measure]:
    return []


def share_at(name: str, condition: str, focal: str) -> Callable[[list[dict]], list[Measure]]:
    """A measure: for each model and n, how many parsed answers to `condition` are at its focal point
    `focal` (a game benchmark such as "cartel", or one of the lens's own)."""

    def measure(rows: list[dict]) -> list[Measure]:
        cells: dict[tuple[str, int], list[bool]] = {}
        for row in rows:
            if row["condition"] == condition and row["value"] is not None:
                cells.setdefault((row["model"], row["n"]), []).append(near(row["value"], row["focal"][focal]))
        return [Measure(name, model, n, sum(hits), len(hits)) for (model, n), hits in cells.items()]

    return measure


@dataclass(frozen=True)
class Lens:
    name: str
    question: str  # what the lens asks, in a line
    slots: dict[str, Slot] = field(default_factory=dict)  # slots this lens adds
    levels: dict[str, dict[str, Level]] = field(default_factory=dict)  # new levels for slots added elsewhere
    conditions: dict[str, Condition] = field(default_factory=dict)  # beside the baseline's
    focal: Callable[[str, int], dict[str, float]] = no_focal  # (condition, n) -> extra focal points
    measure: Callable[[list[dict]], list[Measure]] = no_measures  # table.Replies.rows -> the lens's measures
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

    def condition(self, lens: str, name: str) -> Condition:
        """A lens's condition by name; ValueError naming the ones it has."""
        conditions = self.conditions(lens)
        if name not in conditions:
            raise ValueError(f"lens {lens!r} has no condition {name!r}; it has {', '.join(conditions)}")
        return conditions[name]

    def render(self, condition: Condition, n: int) -> Prompt:
        return render(condition, n, self.slots)

    def focal(self, lens: str, name: str, n: int) -> dict[str, float]:
        """The answers worth counting for a lens's condition: the game's benchmarks, then the lens's own."""
        return {**self.condition(lens, name).game.benchmarks(n), **self.lenses[lens].focal(name, n)}


def build(lenses: Sequence[Lens], core: Mapping[str, Slot] = CORE_SLOTS) -> Registry:
    """Join the lenses' slots, levels, judges and conditions; raise RegistryError, naming the lens, on a clash
    or on a condition that doesn't render (an unknown slot or level, a question the game lacks, an unknown
    field)."""
    names = [lens.name for lens in lenses]
    for lens in lenses:
        if names.count(lens.name) > 1:
            raise _refuse(lens, f"lens {lens.name!r} twice")
    slots = _join_slots(lenses, core)
    registry = Registry(slots, dict(zip(names, lenses, strict=True)), _join_judges(lenses))
    _check_conditions(registry, lenses)
    return registry


def _refuse(lens: Lens, why: str) -> RegistryError:
    return RegistryError(f"lens {lens.name!r}: {why}")


def _join_slots(lenses: Sequence[Lens], core: Mapping[str, Slot]) -> dict[str, Slot]:
    """The core slots and every lens's, then every lens's new levels, so a lens can add levels to a slot
    another lens owns."""
    slots = {name: Slot(slot.anchor, dict(slot.levels)) for name, slot in core.items()}
    for lens in lenses:
        for name, slot in lens.slots.items():
            if name in slots:
                raise _refuse(lens, f"slot {name!r} already exists")
            if slot.anchor not in ANCHORS:
                raise _refuse(
                    lens, f"slot {name!r} has anchor {slot.anchor!r}, not one of {', '.join(ANCHORS)}"
                )
            if slot.levels.get("none") != Level():
                raise _refuse(lens, f"slot {name!r} needs an empty 'none' level")
            slots[name] = Slot(slot.anchor, dict(slot.levels))
    for lens in lenses:
        for name, levels in lens.levels.items():
            if name not in slots:
                raise _refuse(lens, f"no slot {name!r} to add levels to")
            for level, text in levels.items():
                if level in slots[name].levels:
                    raise _refuse(lens, f"slot {name!r} already has level {level!r}")
                slots[name].levels[level] = text
    return slots


def _join_judges(lenses: Sequence[Lens]) -> dict[str, Judge]:
    judges = dict(CORE_JUDGES)
    for lens in lenses:
        for name, judge in lens.judges.items():
            if name in judges:
                raise _refuse(lens, f"judge {name!r} already exists")
            judges[name] = judge
    return judges


def _check_conditions(registry: Registry, lenses: Sequence[Lens]):
    """Each condition name belongs to one lens, renders, and has a prompt of its own within its lens: a lens's
    log keys replies by prompt, so two names for one prompt would share their replies."""
    owner = dict.fromkeys(BASELINE, "the baseline")
    baseline = {registry.render(condition, 2).hash: name for name, condition in BASELINE.items()}
    for lens in lenses:
        seen = dict(baseline)
        for name, condition in lens.conditions.items():
            if name in owner:
                raise _refuse(lens, f"condition {name!r} already belongs to {owner[name]}")
            owner[name] = f"lens {lens.name!r}"
            try:
                prompt = registry.render(condition, 2)
            except (ValueError, KeyError) as e:
                raise _refuse(lens, f"condition {name!r} doesn't render: {e}") from e
            if prompt.hash in seen:
                raise _refuse(lens, f"condition {name!r} renders the prompt of {seen[prompt.hash]!r}")
            seen[prompt.hash] = name
