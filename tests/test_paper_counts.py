"""The counting the criteria's paper sources share, on fixture rows shaped like zerocommcartel.table's: an
answer at or below a focal point, the rows a count takes, one cell's rate against a pooled count, and a table
line per model."""

from paper.data.counts import STANDARD, at, below, chosen, count, line
from paper.ledger import Ledger


def row(value=30.0, model="opus", condition="same", n=2, prompt_hash=None):
    return {
        "model": model,
        "condition": condition,
        "n": n,
        "value": value,
        "prompt_hash": prompt_hash or f"{condition}-{n}",
        "focal": {"nash": 40.0, "cartel": 30.0},
    }


def test_an_answer_is_at_a_focal_point_within_half_a_unit_and_below_it_beyond_that():
    assert [at("cartel")(row(v)) for v in (30.5, 29.5, 30.6)] == [True, True, False]
    assert [below("nash")(row(v)) for v in (39.4, 39.5, 40)] == [True, False, False]


def test_a_count_takes_the_parsed_answers_of_its_conditions_sizes_and_models():
    rows = [
        row(),
        row(None),  # no answer line
        row(condition="diff"),
        row(n=4),
        row(model="nemotron"),  # not one of the five standard models
    ]
    assert chosen(rows, ["same"]) == [rows[0], rows[3]]
    assert chosen(rows, ["same"], ns=[2]) == [rows[0]]
    assert chosen(rows, ["same"], ns=[2], models=None) == [rows[0], rows[4]]


def test_one_cells_count_has_an_interval_and_several_cells_are_pooled(tmp_path):
    ledger = Ledger(tmp_path)
    count(ledger, "cell", [row(30), row(40)], at("cartel"), how="h")
    count(ledger, "both", [row(30), row(30, model="haiku")], at("cartel"), how="h")
    assert set(ledger.entries) == {"cell", "both"}
    assert (ledger.entries["cell"]["kind"], ledger.entries["cell"]["k"], ledger.entries["cell"]["n"]) == (
        "rate",
        1,
        2,
    )
    assert 0 < ledger.entries["cell"]["lo"] < 0.5 < ledger.entries["cell"]["hi"] < 1
    assert (ledger.entries["both"]["kind"], ledger.entries["both"]["k"]) == ("pooled", 2)


def test_a_table_line_counts_each_standard_model_and_all_five_and_records_each_count(tmp_path):
    ledger = Ledger(tmp_path)
    rows = [row(30), row(40), row(30, model="haiku")]
    found = line(ledger, "the label", "crit.same", "n2.cartel", rows, at("cartel"), how="h")
    assert found == ["the label", "1/1", "-", "1/2", "-", "-", "2/3"]
    assert list(STANDARD)[:3] == ["haiku", "sonnet", "opus"]
    assert set(ledger.entries) == {
        "crit.same.haiku.n2.cartel",
        "crit.same.opus.n2.cartel",
        "crit.same.n2.cartel",
    }
    assert ledger.entries["crit.same.n2.cartel"]["kind"] == "pooled"


def test_a_table_line_with_no_rows_shows_dashes_and_records_nothing(tmp_path):
    ledger = Ledger(tmp_path)
    assert line(ledger, "the label", "crit.hub", "n2.cartel", [], at("cartel"), how="h") == [
        "the label",
        *["-"] * 6,
    ]
    assert ledger.entries == {}
