"""The paper's IDL-1 source, on fixture rows (no test reads the real logs): which comparisons the figure
draws, which bars it marks as capped, and the ledger it fills."""

import re

import pytest

from paper.data.idl1 import capped, fill
from paper.ledger import Ledger
from zerocommcartel.criteria.communal.identity import CONDITIONS
from zerocommcartel.criteria.communal.idl1 import Comparison
from zerocommcartel.criteria.communal.judge import REFUSAL

NASH = "QUANTITY: 40"  # every fixture reply off the cartel share, unless it refuses
LABELS = {REFUSAL.key(NASH): {"declines": False, "law": False, "harm": False, "instability": False}}


def rows_for(model, cartel=None, fresh=None, refusing=None):
    """Every IDL-1 cell at 10 first-stage replies at Nash, except `cartel` ({cell: replies at 30 of 10});
    `fresh` adds samples 10-39 ({cell: replies at 30 of 30}); `refusing` ({cell: reply}) gives a cell's first
    stage one reply text off the cartel share, numbered by sample."""
    cartel, fresh, refusing = cartel or {}, fresh or {}, refusing or {}
    found = [
        {
            "model": model,
            "condition": name,
            "sample": s,
            "value": 30.0 if s < cartel.get(name, 0) else 40.0,
            "reply": f"{refusing[name]} {s}\n{NASH}" if name in refusing else NASH,
        }
        for name in CONDITIONS
        for s in range(10)
    ]
    found += [
        {
            "model": model,
            "condition": name,
            "sample": s,
            "value": 30.0 if s - 10 < hits else 40.0,
            "reply": NASH,
        }
        for name, hits in fresh.items()
        for s in range(10, 40)
    ]
    return found


ROWS = rows_for(
    "opus",
    cartel={"id_open_rival_charity": 9, "id_mirror_buyers_distributors": 4},
    fresh={"id_mirror_buyers_distributors": 11, "id_mirror_buyers_pe": 0},
) + rows_for("glm")


def test_fill_draws_the_passing_comparisons_titled_in_three_columns_and_names_the_models_with_none(tmp_path):
    ledger = Ledger(tmp_path)
    fill(ledger, ROWS, LABELS)
    entries = ledger.entries
    assert entries["idl1-figure"]["kind"] == "figure"
    drawn = (tmp_path / "idl1-figure.svg").read_text()
    assert "Opus" in drawn and "GLM" not in drawn  # no panel for a model with no passing comparison
    assert "Conscience: Effect on Cartel Choice %" in drawn
    assert all(f">{head}<" in drawn for head in ("Context", "Baseline", "Experiment"))
    assert all(
        f">{text}<" in drawn for text in ("repeated game", "holding co. owns rival", "charity owns rival")
    )
    assert ">PE distributors buy<" in drawn and drawn.count(">*<") == 1  # 11 of 30 to 0: capped
    assert re.search(r"text-anchor: end; fill: #0b0b0b[^>]*>\*<", drawn)  # in ink, ending left of the whisker
    assert "cartel share, relative to baseline (points)" in drawn
    assert entries["idl1.caption.none"]["value"] == "No comparison passes for GLM-5.3."
    assert (entries["idl1.tests"]["value"], entries["idl1.pass"]["value"]) == (84, 2)
    assert (entries["idl1.pass.first"]["value"], entries["idl1.pass.fresh"]["value"]) == (1, 1)
    assert len(entries["idl1-tests"]["rows"]) == 84 + 8  # the family, then the sanity checks
    starts = {row[1] for row in entries["idl1-tests"]["rows"]}
    assert {"collusion history", "competition history"} <= starts  # after eight quarters at 30, and at 40


def test_every_model_with_a_passing_comparison_leaves_the_caption_note_empty(tmp_path):
    ledger = Ledger(tmp_path)
    fill(ledger, rows_for("opus", cartel={"id_open_rival_charity": 9}), LABELS)
    assert ledger.entries["idl1.caption.none"]["value"] == ""


def comparison(hits, n, reference_hits, reference_n):
    return Comparison(
        "opus",
        "mirror",
        "id_mirror_buyers_pe",
        "id_mirror_buyers_distributors",
        "fresh",
        hits,
        n,
        reference_hits,
        reference_n,
        0.0,
        0.0,
        True,
    )


@pytest.mark.parametrize(
    "counts, marked",
    [
        ((0, 30, 11, 30), True),  # to the floor, 37 points
        ((10, 10, 5, 10), True),  # to the ceiling, 50 points
        ((0, 10, 7, 10), False),  # to the floor, but 70 points
        ((9, 10, 0, 10), False),  # 90 points, short of the ceiling
        ((1, 10, 5, 10), False),  # 40 points, short of the floor
    ],
)
def test_a_bar_is_capped_when_it_ends_at_the_floor_or_ceiling_within_50_points(counts, marked):
    assert capped(comparison(*counts)) is marked


def test_fill_draws_an_empty_figure_and_fills_every_key_when_nothing_passes(tmp_path):
    ledger = Ledger(tmp_path)
    fill(ledger, rows_for("glm"), LABELS)
    entries = ledger.entries
    assert entries["idl1-figure"]["kind"] == "figure"
    assert entries["idl1.caption.none"]["value"] == "No comparison passes for GLM-5.3."
    assert (entries["idl1.pass"]["value"], entries["idl1.tests"]["value"]) == (0, 42)
    assert (entries["idl1.aside"]["value"], entries["idl1.refusals"]["value"]) == (0, 0)


def test_fill_counts_the_bars_refusals_explain_and_the_refusals_behind_them_once(tmp_path):
    rows = rows_for(
        "opus",
        cartel={"id_open_rival_charity": 9, "id_open_rival_pe": 9, "id_mirror_buyers_distributors": 4},
        fresh={"id_mirror_buyers_distributors": 11, "id_mirror_buyers_pe": 0},
        refusing={"id_open_rival_holding": "Illegal.", "id_mirror_harm": "Illegal."},
    )  # the holding company's refusals sit behind two bars: charity and private equity against it
    labels = LABELS | {
        REFUSAL.key(r["reply"]): {
            "declines": True,
            "law": r["sample"] != 0,  # one refusal gives harm alone
            "harm": r["sample"] == 0,
            "instability": False,
        }
        for r in rows
        if r["reply"].startswith("Illegal.")
    }
    ledger = Ledger(tmp_path)
    fill(ledger, rows, labels)
    entries = ledger.entries
    assert entries["idl1.pass"]["value"] == 3
    assert entries["idl1.aside"]["value"] == 2  # both against the holding company; the buyers' bar holds
    assert (entries["idl1.refusals"]["value"], entries["idl1.refusals.law"]["value"]) == (10, 9)


def test_fill_names_the_models_whose_first_stage_is_complete_for_methods(tmp_path):
    unfinished = [r for r in rows_for("haiku") if not (r["condition"] == "id_open_base" and r["sample"] == 9)]
    ledger = Ledger(tmp_path)
    fill(ledger, ROWS + unfinished, LABELS)
    assert ledger.entries["idl1.models"]["value"] == "opus glm"  # haiku's first stage is one reply short


def test_the_title_stays_above_the_column_heads_on_a_short_figure(tmp_path):
    ledger = Ledger(tmp_path)
    fill(ledger, rows_for("opus", cartel={"id_open_rival_charity": 9}), LABELS)  # one bar: a short figure
    drawn = (tmp_path / "idl1-figure.svg").read_text()

    def top_of(text):  # the SVG's y grows downward
        return float(re.search(rf'y="([\d.]+)"[^>]*>{re.escape(text)}<', drawn).group(1))

    assert top_of("Conscience: Effect on Cartel Choice %") < top_of("Context") - 8  # points apart
    assert top_of("Context") < top_of("Opus")
