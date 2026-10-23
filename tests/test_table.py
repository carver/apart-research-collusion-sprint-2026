"""A lens's table, its measure and the synthesis across lenses, over hand-made log rows."""

import pytest

from zerocommcartel.judge import COPY
from zerocommcartel.lens import Lens, Measure, build, share_at
from zerocommcartel.prompt import Condition
from zerocommcartel.table import prepare, synth, table

REG = build(
    [
        Lens(
            "capable",
            "?",
            conditions={"hubjoint": Condition({"disclosure": "hub"}, ask="joint")},
            measure=share_at("joint at cartel", "hubjoint", "cartel"),
        ),
        Lens(
            "communal",
            "?",
            conditions={"dial": Condition({"disclosure": "anyai"}), "out": Condition({"outlet": "decline"})},
            focal=lambda name, n: {"edt": 33.3} if name == "dial" else {},
            measure=lambda rows: [Measure("anything", "haiku", 2, 1, 4)],
        ),
    ]
)


def row(
    lens, condition, value, model="haiku", n=2, sample=0, reply=None, answer="QUANTITY", error=None, hash=None
):
    prompt = REG.render(REG.conditions(lens)[condition], n)
    reply = reply if reply is not None else f"QUANTITY: {value}"
    return {
        "model": model,
        "lens": lens,
        "condition": condition,
        "n": n,
        "sample": sample,
        "prompt_hash": hash or prompt.hash,
        "reply": None if error else reply,
        "answer": None if error else answer,
        "value": None if error else value,
        "error": error,
    }


def cells(markdown):
    """The table's rows as dicts, keyed by its header."""
    lines = [line for line in markdown.splitlines() if line.startswith("|")]
    header = [h.strip() for h in lines[0].strip("|").split("|")]
    return [
        dict(zip(header, (c.strip() for c in line.strip("|").split("|")), strict=True)) for line in lines[2:]
    ]


def cell(markdown, **key):
    (found,) = [c for c in cells(markdown) if all(c[k] == str(v) for k, v in key.items())]
    return found


def show(lens, rows, labels=None):
    return table(REG, prepare(REG, lens, rows, labels or {}))


def test_a_cell_counts_its_answers_at_each_focal_point():
    rows = [row("communal", "same", v, sample=i) for i, v in enumerate([30, 30, 40, 60, 33])]
    c = cell(show("communal", rows), condition="same", model="haiku", n=2)
    assert {k: c[k] for k in ("replies", "parsed", "median", "nash", "cartel", "naive", "other")} == {
        "replies": "5",
        "parsed": "5",
        "median": "33",
        "nash": "1",
        "cartel": "2",
        "naive": "1",
        "other": "1",
    }


def test_a_lens_focal_point_gets_counted_too():
    rows = [row("communal", "dial", v, sample=i) for i, v in enumerate([33.3, 33, 30])]
    assert cell(show("communal", rows), condition="dial")["lens focal"] == "edt 2"


def test_the_cells_follow_the_lens_order_of_conditions_then_n():
    rows = [
        row("communal", "dial", 30),
        row("communal", "same", 30, n=4),
        row("communal", "same", 30),
        row("communal", "base", 40),
    ]
    assert [(c["condition"], c["n"]) for c in cells(show("communal", rows))] == [
        ("base", "2"),
        ("same", "2"),
        ("same", "4"),
        ("dial", "2"),
    ]


def test_an_answer_on_a_text_line_is_counted_apart():
    rows = [
        row("communal", "out", None, reply="DECLINE: no", answer="DECLINE"),
        row("communal", "out", 30, sample=1),
    ]
    c = cell(show("communal", rows), condition="out")
    assert (c["replies"], c["parsed"], c["text answer"]) == ("2", "1", "1")


def test_a_reply_from_an_older_wording_is_left_out_and_reported():
    rows = [row("communal", "same", 30), row("communal", "same", 40, sample=1, hash="0123456789ab")]
    out = show("communal", rows)
    assert cell(out, condition="same")["replies"] == "1"
    assert "1 reply from an older wording" in out


def test_a_retried_call_counts_once_and_a_failure_without_a_retry_is_reported():
    rows = [
        row("communal", "same", None, error="rate limited"),
        row("communal", "same", 30),
        row("communal", "same", None, sample=1, error="rate limited"),
    ]
    out = show("communal", rows)
    assert cell(out, condition="same")["replies"] == "1"
    assert "1 call failed with no reply yet" in out


def test_the_copy_judges_labels_give_the_copy_share():
    rows = [
        row("communal", "same", 30, reply="they copy me\nQUANTITY: 30"),
        row("communal", "same", 40, sample=1),
    ]
    labels = {"copy": {COPY.key("they copy me\nQUANTITY: 30"): {"premise": True, "acts": True}}}
    c = cell(show("communal", rows, labels), condition="same")
    assert (c["judged"], c["% copy"]) == ("1", "100")


def test_mentions_are_shares_of_the_replies():
    rows = [
        row("communal", "same", 30, reply="That is a cartel. QUANTITY: 30"),
        row("communal", "same", 40, sample=1),
    ]
    c = cell(show("communal", rows), condition="same")
    assert (c["% collusion"], c["% antitrust"]) == ("50", "0")


def test_share_at_measures_each_model_and_n():
    rows = [
        row("capable", "hubjoint", 30),
        row("capable", "hubjoint", 40, sample=1),
        row("capable", "hubjoint", 15, n=4),
        row("capable", "hubjoint", 30, model="sonnet"),
        row("capable", "same", 30, sample=2),
    ]
    measures = REG.lenses["capable"].measure(prepare(REG, "capable", rows, {}).rows)
    assert sorted(measures, key=lambda m: (m.model, m.n)) == [
        Measure("joint at cartel", "haiku", 2, 1, 2),
        Measure("joint at cartel", "haiku", 4, 1, 1),
        Measure("joint at cartel", "sonnet", 2, 1, 1),
    ]


def test_synth_joins_each_lens_measure_with_collusion_on_same_pooled_across_lenses():
    capable = prepare(REG, "capable", [row("capable", "same", 30), row("capable", "hubjoint", 30)], {})
    communal = prepare(
        REG, "communal", [row("communal", "same", 40), row("communal", "same", 30, sample=1)], {}
    )
    c = cell(synth(REG, [capable, communal]), model="haiku", n=2)
    assert c == {
        "model": "haiku",
        "n": "2",
        "same at cartel": "2/3",
        "capable: joint at cartel": "1/1",
        "communal: anything": "1/4",
    }


@pytest.mark.parametrize("value, at", [(30.5, True), (29.5, True), (30.6, False)])
def test_an_answer_within_half_a_unit_is_at_the_focal_point(value, at):
    rows = [row("communal", "same", value)]
    assert cell(show("communal", rows), condition="same")["cartel"] == ("1" if at else "0")
