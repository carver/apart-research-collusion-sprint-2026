"""The communal criterion (#41): does the model give up its own profit for the other firm? Its results, as
#41's reporting notes list them, from the rows `zcc table communal` counts.

Under the `same` mirror the cartel share is already the firm's own best answer, so the arms take the mirror
away: a rival whose output is fixed (`fixed_*`, `leave_*`, `run_*` and their neutral questions), a rival
that is a copy only with some chance (the dial), a market record (goodwill). `communal-table` gives the
cartel arms and the null at two firms; the mirror-stated keys pool the pilot's `same` replies (preexisting
work) with the sprint's, as `zerocommcartel.criteria.communal.report` does."""

import re

from paper.data import counts, source
from paper.data.counts import HOW, Arm, at, chosen, count
from paper.ledger import Ledger
from zerocommcartel import cli, logs
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.communal import CONDITIONS, DIAL, DUOPOLY, FIXED, RUN
from zerocommcartel.criteria.communal.measures import states_the_mirror
from zerocommcartel.criteria.communal.report import PILOT_LOG, pilot_same
from zerocommcartel.mentions import MENTIONS

FIXED_RIVAL = [name for name, condition in CONDITIONS.items() if condition.game in (FIXED, RUN)]
# the dial short of certainty: at 100% the mirror point is the cartel share, off the curve
CHANCE = [f"dial{p}" for p in DIAL if p < 100]
SAME = "same model and prompt"
OTHERS = "rivals on other models"
TABLE = [
    Arm(SAME, "same", ["same"], "cartel"),
    Arm(f"{SAME}, not asked to maximize profit", "same_plain", ["same_plain"], "cartel"),
    Arm(f"{SAME}, asked what is best for my firm", "same_best", ["same_best"], "cartel"),
    Arm(f"{SAME}, the other firm can't deviate", "lockstep_same", ["lockstep_same"], "cartel"),
    Arm(
        f"{SAME}, the other firm best-responds: leads, {DUOPOLY.leader():g}",
        "check_same",
        ["check_same"],
        "leader",
    ),
    Arm(f"{SAME}, the other firm checks: at Nash", "hint_same", ["hint_same"], "nash"),
    Arm("you advise both firms, each asks separately", "hub", ["hub"], "cartel"),
    Arm("you advise both firms, the other firm can't deviate", "lockstep_hub", ["lockstep_hub"], "cartel"),
    Arm("a chance the other firm is a copy: on the mirror curve", "dial", CHANCE, "mirror"),
    Arm("a chance the other firm is a copy: on the pair's curve", "dial", CHANCE, "pair"),
    Arm(f"the other firm's output fixed: own best response, {FIXED.best():g}", "fixed", FIXED_RIVAL, "best"),
    Arm(f"the other firm's output fixed: the pair's optimum, {FIXED.pair():g}", "fixed", FIXED_RIVAL, "pair"),
    Arm(f"{OTHERS}, an open-ended market", "repeat_diff", ["repeat_diff"], "cartel"),
    Arm(f"{OTHERS}, eight quarters both at 30", "goodwill_repeat_diff", ["goodwill_repeat_diff"], "cartel"),
    Arm(f"{OTHERS}, that record, the last quarter", "goodwill_last_diff", ["goodwill_last_diff"], "cartel"),
    Arm(
        f"{OTHERS}, only the other firm at 30: cashes in, {DUOPOLY.cash_in():g}",
        "onesided_repeat_diff",
        ["onesided_repeat_diff"],
        "cash in",
    ),
]


def arms_table(ledger: Ledger, rows: list[dict]) -> None:
    counts.arms_table(ledger, "communal", TABLE, rows)


def mirror_stated(ledger: Ledger, same: list[dict]) -> None:
    """Of the `same` replies the copy judge says state the mirror, those at Nash, over every model and per
    model; then the rule judge's order of operations for those at Nash and those at the cartel share."""
    premise = [row for row in same if row["value"] is not None and states_the_mirror(row)]
    how = "parsed `same` replies stating the mirror (the copy judge's premise) at Nash / all such, both sizes"
    count(ledger, "communal.mirror.nash", premise, at("nash"), how)
    for model in sorted({row["model"] for row in premise}):
        mine = [row for row in premise if row["model"] == model]
        count(ledger, f"communal.mirror.{model}.nash", mine, at("nash"), how)
    for focal, order in (("nash", "respond_first"), ("cartel", "equal_first")):
        ruled = [row for row in premise if at(focal)(row) and "rule" in row["labels"]]
        count(
            ledger,
            f"communal.mirror.{focal}.{order}",
            ruled,
            lambda row, order=order: row["labels"]["rule"]["order"] == order,
            how=f"of those at {focal} that the rule judge labelled, its order {order} / all labelled",
        )


def antitrust(ledger: Ledger, rows: list[dict]) -> None:
    """How often Opus mentions antitrust (the pilot's regex) on `hub`, `lockstep_hub` and the goodwill record
    with a future, of every reply."""
    for condition in ("hub", "lockstep_hub", "goodwill_repeat_diff"):
        found = [r for r in rows if r["condition"] == condition and r["model"] == "opus" and r["n"] == 2]
        count(
            ledger,
            f"communal.{condition}.opus.n2.antitrust",
            found,
            lambda row: bool(re.search(MENTIONS["antitrust"], row["reply"], re.I)),
            how="replies matching the antitrust regex (zerocommcartel.mentions) / replies, numbered or not",
        )


def both_sizes(ledger: Ledger, rows: list[dict]) -> None:
    """`same` and the last quarter with rivals on other models, at the cartel share, at two and four firms."""
    for condition in ("same", "last_diff"):
        found = chosen(rows, [condition])
        count(ledger, f"communal.{condition}.cartel", found, at("cartel"), f"{HOW}; five models, both sizes")


@source("communal")
def communal(ledger: Ledger) -> None:
    rows = cli.replies(REGISTRY, "communal", None).rows
    rule_cache = logs.judge_path(logs.log_path("communal"), "rule")
    pilot = pilot_same(REGISTRY, PILOT_LOG, rule_cache).rows
    arms_table(ledger, rows)
    mirror_stated(ledger, pilot + [row for row in rows if row["condition"] == "same"])
    antitrust(ledger, rows)
    both_sizes(ledger, rows)
