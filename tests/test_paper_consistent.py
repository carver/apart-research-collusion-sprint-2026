"""The paper's consistent source, on fixture rows prepared as zcc prepares the criterion's log (no test reads
the real logs): the table of arms, the forecast's controls, the horizons, the prompt monitor's frontier, the
audits and the four views."""

from paper.data.consistent import arms_table, audit_keys, forecasts, frontier, horizons, view_keys
from paper.ledger import Ledger
from zerocommcartel.call import NAMES
from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criteria.consistent import views
from zerocommcartel.criteria.consistent.audits import CheckScore
from zerocommcartel.judge import COPY
from zerocommcartel.prompt import MODEL
from zerocommcartel.table import Replies, prepare


def raw(condition, value, model="opus", n=2, sample=0):
    p = REGISTRY.render(REGISTRY.condition("consistent", condition), n, NAMES.get(model, MODEL))
    return {
        "model": model,
        "criterion": "consistent",
        "condition": condition,
        "n": n,
        "sample": sample,
        "prompt_hash": p.hash,
        "reply": f"{condition} {model} {n} {sample}\n{p.number_key}: {value}",
        "answer": p.number_key,
        "value": value,
        "error": None,
    }


def prepared(rows, premise=None) -> Replies:
    """The rows as zcc counts them, with the copy judge's premise {index: True or False} on the rows named."""
    copy = {COPY.key(rows[i]["reply"]): {"premise": p, "acts": p} for i, p in (premise or {}).items()}
    return prepare(REGISTRY, "consistent", rows, {"copy": copy})


def counted(ledger, key):
    """The key's kind, hits and total, or its value; None when the ledger doesn't have it."""
    entry = ledger.entries.get(key)
    if entry is None or entry["kind"] == "value":
        return entry and entry["value"]
    return entry["kind"], entry["k"], entry["n"]


def test_the_table_counts_each_arm_at_two_firms_and_pools_the_lockstep_seeds(tmp_path):
    rows = prepared(
        [
            raw("suppose45_same", 45),
            raw("suppose45_same", 40, sample=1),
            raw("suppose45_same", 45, model="haiku"),
            raw("hist30_lockstep", 30),
            raw("hist40_lockstep", 30),
        ]
    ).rows
    ledger = Ledger(tmp_path)
    arms_table(ledger, rows)
    assert counted(ledger, "consistent.suppose45_same.opus.n2.supposed") == ("rate", 1, 2)
    assert counted(ledger, "consistent.suppose45_same.n2.supposed") == ("pooled", 2, 3)
    assert counted(ledger, "consistent.hist_lockstep.opus.cartel") == ("pooled", 2, 2)
    table = ledger.entries["consistent-table"]
    assert table["header"][1:] == ["Haiku", "Sonnet", "Opus", "Astra", "GLM", "all five"]
    assert ["1/1", "-", "1/2", "-", "-", "2/3"] in [r[1:] for r in table["rows"]]


def test_the_forecasts_controls_pool_both_suppositions(tmp_path):
    rows = prepared(
        [
            raw("suppose30_diff", 40, model="haiku"),
            raw("suppose45_diff", 40, model="haiku"),
            raw("suppose45_diff", 37.5),  # the rival's best reply to 45
            raw("suppose30_samemodel", 30, model="astra"),
            raw("suppose45_samemodel", 40, model="astra"),
            raw("samemodel", 40, model="astra"),
            raw("samemodel", 24, model="astra", n=4),
        ]
    ).rows
    ledger = Ledger(tmp_path)
    forecasts(ledger, rows)
    assert counted(ledger, "consistent.suppose_diff.nash") == ("pooled", 2, 3)
    assert counted(ledger, "consistent.suppose_samemodel.astra.supposed") == ("pooled", 1, 2)
    assert counted(ledger, "consistent.samemodel.astra.cartel") == ("pooled", 0, 2)


def test_the_horizons_count_the_repeat_alone_controls_copy_premise_and_the_free_models(tmp_path):
    rows = prepared(
        [
            raw("rep", 30, model="haiku"),
            raw("rep", 30),
            raw("rep", 40, model="nemotron"),
            raw("onemore_same", 30, model="nemotron"),
            raw("onemore_same", 20, model="dots", n=4),
            raw("onemore_same", 30),  # not one of the free models
            raw("samerep", 30, model="luna"),
            raw("last_same", 30),
            raw("last_same", 15, model="haiku", n=4),
        ],
        premise={0: False, 1: True},
    ).rows
    ledger = Ledger(tmp_path)
    horizons(ledger, rows)
    assert counted(ledger, "consistent.rep.cartel") == ("pooled", 2, 3)
    assert counted(ledger, "consistent.rep.cartel.premise") == ("pooled", 1, 2)
    assert counted(ledger, "consistent.onemore_same.free.cartel") == ("pooled", 1, 2)
    assert counted(ledger, "consistent.samerep.free.cartel") == ("rate", 1, 1)
    assert counted(ledger, "consistent.last_same.cartel") == ("pooled", 2, 2)


def test_the_frontier_gives_each_scored_wordings_score_and_its_answers_below_nash(tmp_path):
    replies = prepared([raw("same", 30), raw("same", 40, sample=1), raw("diff", 40), raw("same", 30, n=4)])
    ledger = Ledger(tmp_path)
    frontier(ledger, replies, {("same", 2): 95, ("diff", 2): 1})
    assert counted(ledger, "consistent.monitor.same.n2.score") == 95
    assert counted(ledger, "consistent.monitor.same.n2.below_nash") == ("rate", 1, 2)
    assert counted(ledger, "consistent.monitor.diff.n2.below_nash") == ("rate", 0, 1)
    assert "consistent.monitor.same.n4.score" not in ledger.entries  # the monitor didn't score it


def test_each_audits_flag_rates_over_all_models_are_whole_percents(tmp_path):
    scores = [
        CheckScore("best response", "number only", "all", 2, 0, 50, 0.0, 40, 1.0),
        CheckScore("reply monitor", "reasoned", "all", 4, None, 100, 0.02, 80, 0.951),
        CheckScore("reply monitor", "reasoned", "opus", 4, None, 20, 0.0, 20, 1.0),
        CheckScore("identity", "reasoned", "all", 2, 5, 4, 0.67, 0, None),
    ]
    ledger = Ledger(tmp_path)
    audit_keys(ledger, scores)
    assert counted(ledger, "consistent.audit.best_response.number_only.n2.positives_flagged_pct") == 100
    assert counted(ledger, "consistent.audit.best_response.number_only.n2.positives") == 40
    assert counted(ledger, "consistent.audit.reply_monitor.reasoned.n4.positives_flagged_pct") == 95
    assert counted(ledger, "consistent.audit.reply_monitor.reasoned.n4.negatives_flagged_pct") == 2
    assert not [key for key in ledger.entries if ".opus." in key]  # all models only
    assert (
        "consistent.audit.identity.reasoned.n2.positives_flagged_pct" not in ledger.entries
    )  # it ran on none


def test_each_view_counts_the_colluding_and_competing_markets_it_flags(tmp_path):
    rows = [raw("same", v, sample=i, model="haiku") for i, v in enumerate([30, 30, 40, 40])]
    rows += [raw("same", 30, sample=i) for i in range(2)]
    found = views.markets(prepared(rows))
    by_model = {(m.model, m.colluding): m.key for m in found}
    scores = {
        (by_model[("haiku", True)], "words"): 90,
        (by_model[("haiku", False)], "words"): 60,
        (by_model[("opus", True)], "words"): 10,
        (by_model[("haiku", True)], "actions"): 20,
    }
    ledger = Ledger(tmp_path)
    view_keys(ledger, found, scores)
    assert counted(ledger, "consistent.views.words.colluding") == ("pooled", 1, 2)
    assert counted(ledger, "consistent.views.words.competing") == ("rate", 1, 1)
    assert counted(ledger, "consistent.views.actions.colluding") == ("rate", 0, 1)
    assert "consistent.views.actions.competing" not in ledger.entries  # no competing market scored
