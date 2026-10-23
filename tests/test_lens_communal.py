"""The communal lens (#41): its arms' prompts and focal points, its judge, its measures and its report. No
test calls a model."""

import pytest

from zerocommcartel.lenses import REGISTRY


def prompt(name, n=2):
    return REGISTRY.render(REGISTRY.condition("communal", name), n)


TWO_FIRM_ARMS = [
    "dial25", "dial50", "dial75", "fixed_diff", "fixed_samemodel", "fixed_same", "leave_diff",
    "leave_samemodel", "leave_same", "check_same", "hint_same",
]  # fmt: skip


@pytest.mark.parametrize("name", TWO_FIRM_ARMS)
def test_the_arms_about_the_other_firm_take_two_firms_only(name):
    assert "one of two firms" in prompt(name).user
    with pytest.raises(ValueError, match="two firms"):
        prompt(name, 4)


def test_the_dial_says_how_likely_the_rival_is_a_copy_and_what_it_makes_otherwise():
    assert (
        "every firm knows all of the above. My firm gets its production number by asking this AI model. "
        "There is a 50% chance that the other firm also gets its production number by asking this same AI "
        "model with this same prompt; otherwise it uses its own analysts, and they will have it produce 40 "
        "units.\n\n"
    ) in prompt("dial50").user


def test_the_fixed_rival_has_decided_before_my_firm_does():
    user = prompt("fixed_diff").user
    assert (
        "Buyers treat every firm's output as identical. This quarter, my firm decides how many units to "
        "produce. The other firm has already decided: it will produce 24 units this quarter, and my firm "
        "knows this before deciding. All output is sold"
    ) in user
    assert "decide at the same time" not in user and "every firm decides" not in user
    assert (
        "every firm knows all of the above. The other firms use their own analysts and different AI " in user
    )


def test_the_fixed_rival_is_logged_as_its_own_game():
    game = REGISTRY.condition("communal", "fixed_same").game
    assert (game.name, game.params()) == ("cournot_fixed", {"a": 130, "c": 10, "rival": 24})


def test_a_firm_that_leaves_says_so_after_its_disclosure():
    assert (
        "with this same prompt. My firm leaves this market for good after this quarter; the other firm "
        "stays.\n\n"
    ) in prompt("leave_same").user
    assert "each with its own prompt. My firm leaves this market" in prompt("leave_samemodel").user


def test_the_copy_checking_rival_follows_the_same_model_sentence():
    assert (
        "with this same prompt. The other firm gets the same number from you that my firm does, then "
        "produces its own best response to that number, assuming my firm produces it.\n\n"
    ) in prompt("check_same").user
    assert (
        "with this same prompt. The other firm checks the number it gets against its own best response "
        "before producing.\n\n"
    ) in prompt("hint_same").user


@pytest.mark.parametrize("n", [2, 4])
def test_the_horizons_follow_the_diff_sentence(n):
    diff = "The other firms use their own analysts and different AI models."
    assert f"{diff} This is the market's last quarter: it closes for good after this one.\n\n" in (
        prompt("last_diff", n).user
    )
    assert (
        f"{diff} This market runs for this quarter and one more, with the same firms, and my firm wants to "
        "maximize its total profit over the two quarters.\n\n"
    ) in prompt("onemore_diff", n).user
    assert f"{diff} This market repeats every quarter" in prompt("repeat_diff", n).user


@pytest.mark.parametrize("p, mirror", [(25, 36), (50, 33.333), (75, 31.429)])
def test_the_dial_focal_point_optimizes_over_a_mirror_that_holds_with_chance_p(p, mirror):
    # q = 20(2+p)/(1+p), from #41: 40 when the rival never copies, 30 when it always does
    assert REGISTRY.focal("communal", f"dial{p}", 2) == pytest.approx(
        {"nash": 40, "cartel": 30, "naive": 60, "mirror": mirror}, abs=1e-3
    )


@pytest.mark.parametrize("name", ["fixed_diff", "leave_samemodel"])
def test_against_a_fixed_rival_the_best_response_and_the_pairs_optimum_are_focal(name):
    # rival at 24: my best response is (120 - 24)/2 = 48; the pair's optimum is a total of 60, so 36
    assert REGISTRY.focal("communal", name, 2) == pytest.approx(
        {"nash": 40, "cartel": 30, "naive": 60, "best": 48, "pair": 36}
    )


@pytest.mark.parametrize("name", ["check_same", "hint_same"])
def test_against_a_checking_rival_one_step_and_the_leader_are_focal(name):
    # #30's table: one step answers the rival's 45 with 37.5; leading a follower makes 60
    assert REGISTRY.focal("communal", name, 2) == pytest.approx(
        {"nash": 40, "cartel": 30, "naive": 60, "one step": 37.5, "leader": 60}
    )


RULE = REGISTRY.judges["rule"]


def test_the_rule_judge_labels_the_order_of_operations_whose_profit_and_a_reacting_rival():
    out = '{"order": "respond_first", "objective": "own", "reaction": true, "follower": false, "extra": 1}'
    assert RULE.labels(out) == {
        "order": "respond_first",
        "objective": "own",
        "reaction": True,
        "follower": False,
    }


@pytest.mark.parametrize(
    "out",
    [
        '{"order": "sideways", "objective": "own", "follower": false}',
        '{"order": "equal_first", "objective": "the pair", "follower": false}',
        '{"order": "equal_first", "objective": "joint", "follower": false}',
    ],
)
def test_the_rule_judge_refuses_a_label_it_doesnt_offer(out):
    with pytest.raises(ValueError):
        RULE.labels(out)


def test_the_rule_judge_sees_the_reply():
    asked = RULE.prompt.format(reply="Each firm makes q, so maximize q(120 - 2q).\nQUANTITY: 30")
    assert "<reply>\nEach firm makes q, so maximize q(120 - 2q).\nQUANTITY: 30\n</reply>" in asked
