"""The paper's capable source, on fixture rows (no test reads the real logs): what counts as an answer at the
cartel quantity, the ledger each of its three experiments fills, and the three-firm market's replies a cell
and prompt."""

import re

import pytest

from paper.data.capable import (
    at_cartel,
    at_cartel_or_nash,
    fill_capability,
    fill_cell_size,
    fill_history_horizon,
    fill_prompt,
    fill_wordings,
)
from paper.ledger import Ledger


def row(model="opus", condition="quarter_cartel_long", value: float | None = 20.0, sample=0):
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


@pytest.mark.parametrize(
    "value, hit",
    [(20.0, True), (30.0, True), (25.0, False), (29.5, False), (30.5, False), (None, False)],
)
def test_cartel_or_nash_is_an_answer_exactly_at_either(value, hit):
    assert at_cartel_or_nash(row(value=value)) is hit


def test_capability_pools_the_stronger_models_own_answers_and_the_weaker_models_joint_ones(tmp_path):
    rows = [
        row("opus", "quarter_cartel_long_joint", 20.0),
        row("opus", "quarter_cartel_long", 20.0, 0),
        row("opus", "quarter_cartel_long", 30.0, 1),
        row("glm", "quarter_cartel_long_joint", 20.0),
        row("glm", "quarter_cartel_long", 24.0),
        row("commandr", "quarter_cartel_long_joint", 20.0, 0),
        row("commandr", "quarter_cartel_long_joint", 25.0, 1),
        row("commandr", "quarter_cartel_long", 20.0),
        row("llama8b", "quarter_cartel_long_joint", None, 0),  # no answer line: neither
        row("llama8b", "quarter_cartel_long_joint", 30.0, 1),
        row("llama8b", "quarter_cartel_long", 40.0),
    ]
    ledger = Ledger(tmp_path)
    fill_capability(ledger, rows)
    pooled = {key: (e["k"], e["n"]) for key, e in ledger.entries.items() if e["kind"] == "pooled"}
    assert pooled == {"cap9.strong.own.cartel-or-nash": (2, 3), "cap9.weak.joint.other": (2, 4)}


def test_history_horizon_pools_the_answers_at_cartel_or_nash_across_the_grid(tmp_path):
    rows = [
        row(model, f"quarter_{history}_{horizon}", value, sample)
        for model in ("opus", "glm")
        for history in ("cartel", "first")
        for horizon in ("long", "none", "last")
        for sample, value in enumerate((20.0, 30.0, 45.0))
    ]
    rows += [
        row("commandr", "quarter_cartel_long", 20.0),  # a model the figure doesn't draw
        row("opus", "quarter_cartel_long_joint", 20.0),  # a question it doesn't ask
    ]
    ledger = Ledger(tmp_path)
    fill_history_horizon(ledger, rows)
    entry = ledger.entries["cap8.cartel-or-nash"]
    assert (entry["kind"], entry["k"], entry["n"]) == ("pooled", 24, 36)


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


def replies(model: str, condition: str, k: int) -> list[dict]:
    return [row(model, condition, 20.0, sample) for sample in range(k)]


def test_cell_size_counts_the_cells_the_paper_counts_in_each_log(tmp_path):
    logs = {
        "cap9": [
            *replies("opus", "quarter_cartel_long", 2),
            *replies("commandr", "quarter_cartel_long_joint", 2),
            *replies("opus", "plain_own", 1),  # the game-like first version, which CAP-9 no longer counts
        ],
        "cap8": replies("opus", "quarter_cartel_long", 2),  # CAP-9's own prompt, in a run of its own
        "cap10": replies("glm", "plain_own", 2),  # CAP-10 does count it
        "cpl9": [
            *replies("astra", "quarter_none_none_none", 2),
            *replies("astra", "quarter_none_report_none", 2),
            *replies("astra", "quarter_investigating_none_illegal", 1),  # two sentences: a pair
        ],
    }
    ledger = Ledger(tmp_path)
    fill_cell_size(ledger, logs)
    assert ledger.entries.get("capable.cells.replies", {}).get("value") == "2"


def test_cell_size_gives_the_fewest_and_most_when_cells_differ(tmp_path):
    logs = {
        "cap9": replies("opus", "quarter_cartel_long", 3),
        "cap8": replies("glm", "quarter_first_last", 1),
        "cap10": [],
        "cpl9": [],
    }
    ledger = Ledger(tmp_path)
    fill_cell_size(ledger, logs)
    assert ledger.entries.get("capable.cells.replies", {}).get("value") == "1 to 3"


def test_prompt_is_the_collusive_cell_as_zcc_show_prints_it(tmp_path):
    ledger = Ledger(tmp_path)
    fill_prompt(ledger)
    text = ledger.entries.get("capable.prompt.quarter", {}).get("text", "")
    assert text.startswith(
        "$ bin/zcc show capable quarter_cartel_long 3\n"
        "[system] You are the production manager at Alder Industries.\n\n"
        "Alder Industries is one of three companies"
    )
    assert "Previous quarter: Alder Industries (your company) produced 20 tonnes" in text
    assert "There will be many more quarters after this one." in text


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
