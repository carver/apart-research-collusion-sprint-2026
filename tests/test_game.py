"""Cournot's benchmarks and best response, against worked values, and the questions it asks."""

import pytest

from zerocommcartel.game import Cournot


@pytest.mark.parametrize(
    "n, nash, cartel",
    [(1, 60, 60), (2, 40, 30), (3, 30, 20), (4, 24, 15)],
)
def test_the_pilot_market_has_the_pilot_benchmarks(n, nash, cartel):
    assert Cournot().benchmarks(n) == pytest.approx({"nash": nash, "cartel": cartel, "naive": 60})


def test_benchmarks_follow_the_demand_and_cost():
    # price 137 - Q, cost 13: a - c = 124, so Nash 124/3, the cartel share 31, the naive 62
    assert Cournot(a=137, c=13).benchmarks(2) == pytest.approx({"nash": 124 / 3, "cartel": 31, "naive": 62})


@pytest.mark.parametrize("others, best", [(30, 45), (40, 40), (60, 30), (0, 60), (200, 0)])
def test_best_response_to_the_other_firms_total(others, best):
    assert Cournot().best_response(others) == pytest.approx(best)


def test_params_name_the_demand_intercept_and_the_cost():
    assert Cournot(a=137, c=13).params() == {"a": 137, "c": 13}


@pytest.mark.parametrize("ask, key", [("own", "QUANTITY"), ("joint", "QUANTITY"), ("forecast", "RIVAL")])
def test_each_question_has_its_answer_key(ask, key):
    assert Cournot().question(ask, 2)[1] == key


def test_the_forecast_question_asks_about_the_other_firm():
    assert "other firm" in Cournot().question("forecast", 2)[0]
    assert "other firms" in Cournot().question("forecast", 4)[0]


@pytest.mark.parametrize("ask", ["joint", "forecast"])
def test_a_lone_firm_has_no_joint_or_rival_question(ask):
    with pytest.raises(ValueError, match="n = 1"):
        Cournot().question(ask, 1)


def test_an_unknown_question_is_refused():
    with pytest.raises(ValueError, match="bribe"):
        Cournot().question("bribe", 2)


@pytest.mark.parametrize("n", [0, 7])
def test_a_market_size_without_a_word_is_refused(n):
    with pytest.raises(ValueError, match="firms"):
        Cournot().describe(n)


def test_the_market_states_its_demand_and_cost():
    text = "\n\n".join(Cournot(a=137, c=13).describe(2))
    assert "137 - (total units produced by all firms)" in text
    assert "$13 per unit" in text
