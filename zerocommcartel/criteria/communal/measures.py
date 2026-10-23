"""The communal criterion's measures, each hits of total per model and market size (`zcc synth` shows them).

mirror-stated nash         `same` replies that state the copy premise (the copy judge's `premise`) and
                           still answer Nash: the mirror holds and the model defects anyway (#41)
gives up to a fixed rival  of the `fixed_diff` answers the rule judge has labelled, those below the best
                           response to the rival's fixed output, down to the pair's optimum, that it says
                           serve the pair: own profit given up for the pair, with no mirror
last-round cartel          `last_diff` answers at the cartel share: no mirror and no future, so the
                           cartel share is pure sacrifice
"""

from collections.abc import Callable

from zerocommcartel.criterion import NEAR, Measure, near, share_at


def share(
    name: str, condition: str, hit: Callable[[dict], bool], counted: Callable[[dict], bool] = lambda row: True
) -> Callable[[list[dict]], list[Measure]]:
    """A measure: for each model and n, how many parsed, `counted` answers to `condition` are a `hit`."""

    def measure(rows: list[dict]) -> list[Measure]:
        cells: dict[tuple[str, int], list[bool]] = {}
        for row in rows:
            if row["condition"] == condition and row["value"] is not None and counted(row):
                cells.setdefault((row["model"], row["n"]), []).append(hit(row))
        return [Measure(name, model, n, sum(hits), len(hits)) for (model, n), hits in cells.items()]

    return measure


def states_the_mirror(row: dict) -> bool:
    return row["labels"].get("copy", {}).get("premise") is True


def gives_up(row: dict) -> bool:
    """Below the best response, down to the pair's optimum, and for the pair by the rule judge's reading. An
    answer in that range can also come from ignoring the rival's decided output (Nash, 40) or from a slip, so
    the number alone doesn't say."""
    in_range = row["focal"]["pair"] - NEAR <= row["value"] < row["focal"]["best"] - NEAR
    return in_range and row["labels"].get("rule", {}).get("objective") in ("joint", "both")


MEASURES = [
    share(
        "mirror-stated nash", "same", lambda row: near(row["value"], row["focal"]["nash"]), states_the_mirror
    ),
    share("gives up to a fixed rival", "fixed_diff", gives_up, lambda row: "rule" in row["labels"]),
    share_at("last-round cartel", "last_diff", "cartel"),
]


def measures(rows: list[dict]) -> list[Measure]:
    return [m for measure in MEASURES for m in measure(rows)]
