"""The criterion registry: it joins the criteria's slots, levels and conditions, and refuses two criteria
claiming the same one, so each criterion's owner can work in its own folder."""

import pytest

from zerocommcartel.criteria import REGISTRY
from zerocommcartel.criterion import BASELINE, Criterion, RegistryError, build
from zerocommcartel.game import Cournot
from zerocommcartel.judge import Judge
from zerocommcartel.prompt import CORE_SLOTS, Condition, Level, Slot, render

BUYER = Slot("context", {"none": Level(), "hospital": Level("Our buyers are hospitals.")})
HARM = Judge("harm", "Who loses?\n{reply}", {"type": "object", "required": ["harm"]})


def criterion(name, **kw):
    return Criterion(name, f"does {name} matter?", **kw)


def test_a_criterion_slot_and_its_conditions_render():
    reg = build(
        [
            criterion(
                "compliant", slots={"buyer": BUYER}, conditions={"hosp": Condition({"buyer": "hospital"})}
            )
        ]
    )
    prompt = reg.render(reg.conditions("compliant")["hosp"], 2)
    assert "of the above. Our buyers are hospitals.\n\n" in prompt.user


def test_every_criterion_gets_the_baseline_conditions_first():
    reg = build([criterion("communal", conditions={"dial": Condition({"disclosure": "anyai"})})])
    assert list(reg.conditions("communal")) == ["base", "diff", "same", "dial"]


def test_the_baseline_renders_the_same_prompt_in_every_criterion():
    reg = build([criterion("a"), criterion("b")])
    for name in BASELINE:
        a, b = (reg.render(reg.conditions(x)[name], 2) for x in ("a", "b"))
        assert a == b == render(BASELINE[name], 2, CORE_SLOTS)


def test_a_criterion_can_add_a_level_to_a_core_slot():
    reg = build(
        [
            criterion(
                "consistent",
                levels={"disclosure": {"rivalprompt": Level("Here is my rival's prompt.")}},
                conditions={"shown": Condition({"disclosure": "rivalprompt"})},
            )
        ]
    )
    assert "Here is my rival's prompt." in reg.render(reg.conditions("consistent")["shown"], 2).user


def test_a_criterion_can_use_a_slot_from_another():
    reg = build(
        [
            criterion("compliant", slots={"buyer": BUYER}),
            criterion(
                "communal", conditions={"hosp_same": Condition({"buyer": "hospital", "disclosure": "same"})}
            ),
        ]
    )
    assert "Our buyers are hospitals." in reg.render(reg.conditions("communal")["hosp_same"], 2).user


def test_focal_points_are_the_games_plus_the_criteria():
    reg = build(
        [
            criterion(
                "communal",
                conditions={"dial": Condition({"disclosure": "anyai"})},
                focal=lambda name, n: {"edt": 33.3} if name == "dial" else {},
            )
        ]
    )
    assert reg.focal("communal", "dial", 2) == pytest.approx(
        {"nash": 40, "cartel": 30, "naive": 60, "edt": 33.3}
    )
    assert reg.focal("communal", "base", 2) == pytest.approx({"nash": 40, "cartel": 30, "naive": 60})


def test_a_criterion_judge_joins_the_core_judges():
    assert set(build([criterion("compliant", judges={"harm": HARM})]).judges) == {"copy", "harm"}


def test_focal_points_follow_the_conditions_game():
    reg = build([criterion("capable", conditions={"odd": Condition(game=Cournot(a=137, c=13))})])
    assert reg.focal("capable", "odd", 2)["cartel"] == pytest.approx(31)


@pytest.mark.parametrize(
    "criteria, match",
    [
        ([criterion("a"), criterion("a")], "criterion 'a' twice"),
        ([criterion("a", slots={"disclosure": BUYER})], "slot 'disclosure'"),
        ([criterion("a", slots={"buyer": BUYER}), criterion("b", slots={"buyer": BUYER})], "slot 'buyer'"),
        ([criterion("a", levels={"disclosure": {"same": Level("x")}})], "level 'same'"),
        (
            [
                criterion("a", levels={"horizon": {"last": Level("x")}}),
                criterion("b", levels={"horizon": {"last": Level("y")}}),
            ],
            "level 'last'",
        ),
        ([criterion("a", levels={"mood": {"happy": Level("x")}})], "slot 'mood'"),
        ([criterion("a", judges={"copy": HARM})], "judge 'copy'"),
        ([criterion("a", judges={"harm": HARM}), criterion("b", judges={"harm": HARM})], "judge 'harm'"),
        ([criterion("a", conditions={"same": Condition()})], "condition 'same'"),
        (
            [criterion("a", conditions={"same2": Condition({"disclosure": "same"})})],
            "'same2' renders the prompt of 'same'",
        ),
        (
            [
                criterion(
                    "a",
                    conditions={
                        "x": Condition({"disclosure": "anyai"}),
                        "y": Condition({"disclosure": "anyai"}),
                    },
                )
            ],
            "'y' renders the prompt of 'x'",
        ),
        (
            [criterion("a", conditions={"x": Condition()}), criterion("b", conditions={"x": Condition()})],
            "condition 'x'",
        ),
        ([criterion("a", conditions={"x": Condition({"disclosure": "telepathy"})})], "telepathy"),
        ([criterion("a", conditions={"x": Condition(ask="bribe")})], "bribe"),
        ([criterion("a", slots={"buyer": Slot("context", {"hospital": Level("x")})})], "'none'"),
        ([criterion("a", slots={"buyer": Slot("context", {"none": Level("x")})})], "'none'"),
        ([criterion("a", slots={"buyer": Slot("margin", {"none": Level()})})], "anchor 'margin'"),
        (
            [
                criterion(
                    "a",
                    levels={"disclosure": {"odd": Level("{rivals} ask you")}},
                    conditions={"x": Condition({"disclosure": "odd"})},
                )
            ],
            "rivals",
        ),
    ],
)
def test_conflicts_and_mistakes_are_refused_and_name_the_criterion(criteria, match):
    with pytest.raises(RegistryError, match=match) as err:
        build(criteria)
    assert "'a'" in str(err.value) or "'b'" in str(err.value)


def test_the_criteria_build():
    assert list(REGISTRY.criteria) == ["capable", "compliant", "communal", "consistent", "conceptualization"]
