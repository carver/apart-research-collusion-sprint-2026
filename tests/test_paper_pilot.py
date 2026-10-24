"""The paper's pilot source, on fixture rows (no test reads the pilot's log): an answer is at the cartel share
when it is within half a unit of 60/n, and the cells hold Claude's Cournot replies by arm, model and market
size."""

from paper.data.pilot import at_cartel, cells


def row(model="opus", arm="same", n=2, value=30.0, game="cournot", reply="QUANTITY: 30", sample=0):
    return {
        "model": model,
        "arm": arm,
        "n": n,
        "value": value,
        "game": game,
        "reply": reply,
        "sample": sample,
    }


def test_an_answer_is_at_the_cartel_share_within_half_a_unit():
    assert at_cartel(row(n=2, value=30.4))
    assert at_cartel(row(n=4, value=15))
    assert not at_cartel(row(n=2, value=40))  # Nash
    assert not at_cartel(row(n=4, value=16))
    assert not at_cartel(row(value=None))  # no answer line


def test_cells_hold_claudes_cournot_replies_by_arm_model_and_market_size():
    rows = [
        row(sample=0),
        row(sample=1, value=40),
        row(n=4, value=15),
        row(model="haiku", arm="base"),
        row(model="astra"),  # not Claude
        row(game="bertrand"),
        row(n=1, value=60),  # the lone firm: no rivals
        row(reply=None, value=None),  # a call that failed
    ]
    grouped = cells(rows)
    assert sorted(grouped) == [("base", "haiku", 2), ("same", "opus", 2), ("same", "opus", 4)]
    assert [r["value"] for r in grouped[("same", "opus", 2)]] == [30.0, 40]
