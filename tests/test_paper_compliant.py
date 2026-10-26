"""The paper's compliant source, on fixture rows (no test reads the real logs): the cells it counts."""

from paper.data.compliant import CONTROL, MODELS, ROWS, fill
from paper.ledger import Ledger


def row(model, condition, value):
    return {
        "model": model,
        "condition": condition,
        "sample": 0,
        "prompt_hash": f"hash-{condition}-{model}",
        "value": value,
        "focal": {"cartel": 20.0, "nash": 30.0, "naive": 60.0},
    }


def test_fill_counts_each_figured_cell_and_leaves_the_rest_of_cpl9_out(tmp_path):
    figured = [condition for condition, _ in ROWS if condition]
    rows = [
        row(model, condition, 20.0 if condition == CONTROL else 30.0)
        for model in MODELS
        for condition in figured
    ]
    rows += [
        row("opus", "quarter_investigating_report_none", 20.0),  # a crossed cell the figure doesn't draw
        row("opus", "env_none_none_none", 20.0),  # the game-like first version
        row("haiku", CONTROL, 20.0),  # a model the figure doesn't draw
    ]
    ledger = Ledger(tmp_path)
    fill(ledger, rows)
    rates = {
        key: (entry["k"], entry["n"]) for key, entry in ledger.entries.items() if entry["kind"] == "rate"
    }
    assert len(rates) == len(MODELS) * len(figured)
    assert {key for key, count in rates.items() if count[0]} == {
        f"cpl9.{model}.none_none_none" for model in MODELS
    }
    assert rates["cpl9.glm.investigating_none_illegal"] == (0, 1)
    assert (tmp_path / "cpl9-figure.svg").exists()


def test_fill_counts_a_cited_cell_the_figure_does_not_draw(tmp_path):
    figured = [condition for condition, _ in ROWS if condition]
    rows = [row(model, condition, 20.0) for model in MODELS for condition in figured]
    rows += [
        row("glm", "quarter_none_report_illegal", 20.0),
        row("glm", "quarter_none_report_illegal", 30.0),
    ]
    ledger = Ledger(tmp_path)
    fill(ledger, rows)
    cited = ledger.entries.get("cpl9.glm.none_report_illegal")
    assert cited is not None and (cited["k"], cited["n"]) == (1, 2)
    assert (tmp_path / "cpl9-figure.svg").exists()
