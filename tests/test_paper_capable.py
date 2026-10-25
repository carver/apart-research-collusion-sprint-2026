"""The paper's capable source, on fixture rows (no test reads the real logs): what counts as an answer at the
cartel quantity, and the ledger each of its three experiments fills."""

import re

import pytest

from paper.data.capable import at_cartel, fill_capability, fill_history_horizon, fill_wordings
from paper.ledger import Ledger


def row(model="opus", condition="quarter_cartel_long", value=20.0, sample=0):
    return {
        "model": model,
        "condition": condition,
        "sample": sample,
        "prompt_hash": f"hash-{condition}-{model}",
        "value": value,
        "focal": {"cartel": 20.0, "nash": 30.0, "naive": 60.0},
    }


@pytest.mark.parametrize(
    "value, hit",
    [(20.0, True), (19.5, False), (20.5, False), (30.0, False), (None, False)],
)
def test_only_an_answer_exactly_at_the_cartel_quantity_counts(value, hit):
    assert at_cartel(row(value=value)) is hit


def test_capability_counts_each_models_two_questions_and_draws_a_square_image(tmp_path):
    rows = [
        row("opus", "quarter_cartel_long_joint", 20.0, 0),
        row("opus", "quarter_cartel_long_joint", 20.0, 1),
        row("opus", "quarter_cartel_long", 20.0, 0),
        row("opus", "quarter_cartel_long", 30.0, 1),
        row("commandr", "quarter_cartel_long_joint", 25.0, 0),
        row("commandr", "quarter_cartel_long", 20.0, 0),
        row("commandr", "plain_own", 20.0, 0),  # the game-like first version, which the figure leaves out
    ]
    ledger = Ledger(tmp_path)
    fill_capability(ledger, rows)
    counts = {
        key: (entry["k"], entry["n"]) for key, entry in ledger.entries.items() if entry["kind"] == "rate"
    }
    assert counts == {
        "cap9.opus.joint": (2, 2),
        "cap9.opus.own": (1, 2),
        "cap9.commandr.joint": (0, 1),
        "cap9.commandr.own": (1, 1),
    }
    svg = (tmp_path / "cap9-figure.svg").read_text()
    size = re.search(r'<svg[^>]* width="([\d.]+)pt" height="([\d.]+)pt"', svg)
    assert size and size[1] == size[2]


def test_history_horizon_counts_each_models_six_cells(tmp_path):
    rows = [
        row(
            model,
            f"quarter_{history}_{horizon}",
            20.0 if (model, history, horizon) == ("glm", "first", "long") else 30.0,
        )
        for model in ("opus", "glm")
        for history in ("cartel", "first")
        for horizon in ("long", "none", "last")
    ]
    ledger = Ledger(tmp_path)
    fill_history_horizon(ledger, rows)
    hits = {key for key, entry in ledger.entries.items() if entry["kind"] == "rate" and entry["k"]}
    assert hits == {"cap8.glm.first.long"}
    assert sum(entry["kind"] == "rate" for entry in ledger.entries.values()) == 12
    assert (tmp_path / "cap8-figure.svg").exists()


def test_wordings_table_has_a_row_per_model_and_a_column_per_wording(tmp_path):
    rows = [
        row("astra", "quarter_cartel_long", 30.0),
        row("astra", "game_cartel_long", 20.0),
        row("astra", "plain_own", 20.0),
        row("opus", "quarter_cartel_long", 20.0),
        row("opus", "game_cartel_long", 20.0),
        row("opus", "plain_own", 30.0),
    ]
    ledger = Ledger(tmp_path)
    fill_wordings(ledger, rows)
    table = ledger.entries["cap10-table"]
    assert table["header"] == ["model", "business", "game words", "standard game text"]
    assert table["rows"] == [["Opus", "1/1", "1/1", "0/1"], ["GPT-6 Astra", "0/1", "1/1", "1/1"]]
