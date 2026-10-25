"""The paper's cross-model source, on fixture rows (no test reads the real logs): which cells its figure draws
and the ledger it fills."""

from paper.data.crossmodel import fill
from paper.ledger import Ledger
from zerocommcartel.criteria.communal.identity import CONDITIONS
from zerocommcartel.criteria.communal.judge import REFUSAL


def rows_for(model, cartel=None, fresh=None):
    """Every IDL-1 cell at 10 first-stage replies at Nash, except `cartel` ({cell: replies at 30 of 10});
    `fresh` adds samples 10-39 ({cell: replies at 30 of 30}). Each reply's text is its own."""
    cartel, fresh = cartel or {}, fresh or {}
    found = [
        {"model": model, "condition": name, "sample": s, "value": 30.0 if s < cartel.get(name, 0) else 40.0}
        for name in CONDITIONS
        for s in range(10)
    ]
    found += [
        {"model": model, "condition": name, "sample": s, "value": 30.0 if s - 10 < hits else 40.0}
        for name, hits in fresh.items()
        for s in range(10, 40)
    ]
    return [row | {"reply": f"{row['model']} {row['condition']} {row['sample']}"} for row in found]


def labels_for(rows, refusing=()):
    """Every reply off the cartel share labelled: (model, cell) pairs in `refusing` decline it as illegal."""
    return {
        REFUSAL.key(r["reply"]): {
            "declines": (r["model"], r["condition"]) in refusing,
            "law": (r["model"], r["condition"]) in refusing,
            "harm": False,
            "instability": False,
        }
        for r in rows
        if r["value"] != 30.0
    }


GAP = {"id_mirror_buyers_towns": 10, "id_mirror_buyers_hospitals": 10}  # 10 of 10, against Haiku's 0


ROWS = (
    rows_for(
        "haiku", fresh={"id_mirror_buyers_towns": 0, "id_mirror_buyers_hospitals": 15, "id_mirror_base": 30}
    )
    + rows_for("sonnet", GAP, {"id_mirror_buyers_towns": 30, "id_mirror_buyers_hospitals": 15})
    + rows_for(
        "glm", GAP, {"id_mirror_buyers_towns": 0, "id_mirror_buyers_hospitals": 15, "id_mirror_base": 30}
    )
)
REFUSING = {("glm", "id_mirror_buyers_towns")}  # GLM's towns: every fresh reply refused


def test_fill_draws_the_confirmed_cells_with_their_starts_and_counts(tmp_path):
    ledger = Ledger(tmp_path)
    fill(ledger, ROWS, labels_for(ROWS, REFUSING))
    entries = ledger.entries
    assert entries["idl1-cross-figure"]["kind"] == "figure"
    drawn = (tmp_path / "idl1-cross-figure.svg").read_text()
    assert "same prompt: towns buy" in drawn and "hospitals buy" not in drawn  # 15 of 30 each: not confirmed
    assert "GLM-5.3: all refused" in drawn and "0/30" in drawn
    assert drawn.count("(30/30)") == 2  # the start's count, GLM's too though it refused every towns reply
    assert (entries["idl1.cross.cells"]["value"], entries["idl1.cross.first"]["value"]) == (62, 2)
    assert (entries["idl1.cross.confirmed"]["value"], entries["idl1.cross.unconfirmed"]["value"]) == (1, 0)
    assert (entries["idl1.cross.fresh"]["value"], entries["idl1.cross.thin"]["value"]) == (30, 5)
    assert entries["idl1.cross.caption.none"]["value"] == ""


def test_fill_gives_the_fresh_replies_as_a_range_when_the_models_differ(tmp_path):
    short = [
        r
        for r in ROWS
        if (r["model"], r["condition"], r["sample"]) != ("sonnet", "id_mirror_buyers_towns", 39)
    ]
    ledger = Ledger(tmp_path)
    fill(ledger, short, labels_for(short, REFUSING))
    assert ledger.entries["idl1.cross.fresh"]["value"] == "29 to 30"


def test_fill_draws_an_empty_figure_when_no_cell_holds(tmp_path):
    rows = rows_for("haiku") + rows_for("glm")
    ledger = Ledger(tmp_path)
    fill(ledger, rows, labels_for(rows))
    entries = ledger.entries
    assert entries["idl1-cross-figure"]["kind"] == "figure"
    assert (entries["idl1.cross.confirmed"]["value"], entries["idl1.cross.first"]["value"]) == (0, 0)
    assert entries["idl1.cross.caption.none"]["value"] == "No cell holds on its fresh replies."
