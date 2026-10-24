"""The consistent criterion (#42): does the model expect rivals that ask the same model to answer as it does?
Its results, as #42's two results comments give them, from the rows `zcc table consistent` counts.

`consistent-table` gives the conditional forecast, the twin, the last quarter, the seeded history and the
number-only arm at two firms. The other keys: the forecast's controls, the repeat-alone control (with the
free models the pilot pointed to), #31's prompt monitor against the answers below Nash, #33's audits, and
sprint question 2.2's four views of one monitor."""

from paper.data import counts, source
from paper.data.counts import HOW, Arm, at, below, chosen, count
from paper.ledger import Ledger
from zerocommcartel import cli, logs
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.communal.measures import states_the_mirror
from zerocommcartel.criteria.consistent import DUOPOLY, SEEDS, SUPPOSED, audits, monitor, views
from zerocommcartel.criteria.consistent.audits import CheckScore
from zerocommcartel.table import Replies

FREE = ("nemotron", "dots", "luna")  # the free models the repeat-alone prediction named (#42)
SUPPOSE, SEED = SUPPOSED[-1], SEEDS[0]
SAME, OWN = "same model and prompt", "same model, own prompts"
FOLLOWS = f"forecast follows a supposed {SUPPOSE}"
TABLE = [
    *(
        Arm(f"{says}: {FOLLOWS}", f"suppose{SUPPOSE}_{d}", [f"suppose{SUPPOSE}_{d}"], "supposed")
        for d, says in (("diff", "rivals on other models"), ("samemodel", OWN), ("same", SAME))
    ),
    Arm(OWN, "samemodel", ["samemodel"], "cartel"),
    Arm(f"{OWN}, the other firm's prompt says so too", "twin_informed", ["twin_informed"], "cartel"),
    Arm(f"{OWN}, the other firm's prompt doesn't", "twin", ["twin"], "cartel"),
    Arm(f"{SAME}, the market's last quarter", "last_same", ["last_same"], "cartel"),
    Arm(
        f"{SAME}; it gave {SEED} in 9 of 10 runs: at {DUOPOLY.best_response(SEED):g}",
        f"hist{SEED}_same",
        [f"hist{SEED}_same"],
        "best",
    ),
    Arm(
        f"{SAME}, the other firm can't deviate, either seed",
        "hist_lockstep",
        [f"hist{x}_lockstep" for x in SEEDS],
        "cartel",
    ),
    Arm(f"{SAME}, number only", "same_numonly", ["same_numonly"], "cartel"),
]


def arms_table(ledger: Ledger, rows: list[dict]) -> None:
    counts.arms_table(ledger, "consistent", TABLE, rows)


def forecasts(ledger: Ledger, rows: list[dict]) -> None:
    """The conditional forecast's controls: forecasts at Nash under `diff`, and Astra's forecasts and own
    answers under `samemodel`."""
    diff = chosen(rows, [f"suppose{x}_diff" for x in SUPPOSED], ns=[2])
    count(ledger, "consistent.suppose_diff.nash", diff, at("nash"), f"{HOW}; both suppositions, five models")
    astra = chosen(rows, [f"suppose{x}_samemodel" for x in SUPPOSED], ns=[2], models=["astra"])
    count(ledger, "consistent.suppose_samemodel.astra.supposed", astra, at("supposed"), f"{HOW}; both")
    own = chosen(rows, ["samemodel"], models=["astra"])
    count(ledger, "consistent.samemodel.astra.cartel", own, at("cartel"), f"{HOW}; both market sizes")


def horizons(ledger: Ledger, rows: list[dict]) -> None:
    """The repeat-alone control (`rep`, every model run) and the copy premise in its cartel answers; one more
    quarter against an open-ended market for the free models; the last quarter."""
    rep = chosen(rows, ["rep"], models=None)
    count(ledger, "consistent.rep.cartel", rep, at("cartel"), f"{HOW}; every model, both sizes")
    judged = [row for row in rep if at("cartel")(row) and "copy" in row["labels"]]
    count(
        ledger,
        "consistent.rep.cartel.premise",
        judged,
        states_the_mirror,
        how="cartel answers to rep that state the copy premise (the copy judge) / those it judged",
    )
    for condition in ("onemore_same", "samerep"):
        found = chosen(rows, [condition], models=FREE)
        count(ledger, f"consistent.{condition}.free.cartel", found, at("cartel"), f"{HOW}; {', '.join(FREE)}")
    found = chosen(rows, ["last_same"])
    count(ledger, "consistent.last_same.cartel", found, at("cartel"), f"{HOW}; five models, both sizes")


def frontier(ledger: Ledger, replies: Replies, scores: dict[tuple[str, int], int]) -> None:
    """#31's frontier: each wording the prompt monitor scored, its score, and the standard models' answers to
    it below Nash."""
    for wording in monitor.frontier_rows(REGISTRY, replies, scores):
        stem = f"consistent.monitor.{wording['condition']}.n{wording['n']}"
        how = f"the prompt monitor's score of the firm's prompt, 0-100, flagged at {monitor.THRESHOLD}"
        ledger.value(f"{stem}.score", wording["suspicion"], how=how)
        found = chosen(replies.rows, [wording["condition"]], ns=[wording["n"]], models=monitor.STANDARD)
        if found:
            how = "parsed answers more than 0.5 below Nash / parsed answers; the five standard models"
            count(ledger, f"{stem}.below_nash", found, below("nash"), how)


def audit_keys(ledger: Ledger, scores: list[CheckScore]) -> None:
    """#33's audits over all models: the positives and negatives each check ran on, and its mean flag rate on
    each as a whole percent."""
    for s in scores:
        if s.model != "all":
            continue
        stem = f"consistent.audit.{s.check.replace(' ', '_')}.{s.group.replace(' ', '_')}.n{s.n}"
        for side, total, rate in (
            ("positives", s.positives, s.positives_flagged),
            ("negatives", s.negatives, s.negatives_flagged),
        ):
            ledger.value(f"{stem}.{side}", total, how=f"{side} the check ran on (audits.score)")
            if rate is not None:
                ledger.value(f"{stem}.{side}_flagged", round(100 * rate), how=f"mean flag rate on {side}, %")


def view_keys(ledger: Ledger, markets: list[views.Market], scores: views.Scores) -> None:
    """Sprint question 2.2: per view, the colluding and the competing markets the monitor scored, and how many
    of each it flags."""
    for view in views.VIEWS:
        for colluding, side in ((True, "colluding"), (False, "competing")):
            found = [
                {
                    "model": m.model,
                    "prompt_hash": m.firms[0]["prompt_hash"],
                    "flagged": scores[(m.key, view)] >= monitor.THRESHOLD,
                }
                for m in markets
                if m.colluding == colluding and (m.key, view) in scores
            ]
            if found:
                how = f"{side} markets scored {monitor.THRESHOLD} or more / those scored in the view"
                count(ledger, f"consistent.views.{view}.{side}", found, lambda row: row["flagged"], how)


@source("consistent")
def consistent(ledger: Ledger) -> None:
    replies = cli.replies(REGISTRY, "consistent", None)
    log = logs.log_path("consistent")
    arms_table(ledger, replies.rows)
    forecasts(ledger, replies.rows)
    horizons(ledger, replies.rows)
    cells = monitor.own_number_cells(REGISTRY, replies)
    frontier(ledger, replies, monitor.cached_scores(REGISTRY, cells, logs.judge_path(log, "monitor")))
    audit_keys(ledger, audits.score(replies))
    found = views.markets(replies)
    caches = (logs.judge_path(log, "views"), logs.judge_path(log, "report"))
    view_keys(ledger, found, views.cached_scores(found, *caches))
