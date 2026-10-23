"""The lens registry: it joins the lenses' slots, levels and conditions, and refuses two lenses claiming the
same one, so each lens's owner can work in its own folder."""

import pytest

from zerocommcartel.game import Cournot
from zerocommcartel.judge import Judge
from zerocommcartel.lens import BASELINE, Lens, RegistryError, build
from zerocommcartel.lenses import REGISTRY
from zerocommcartel.prompt import CORE_SLOTS, Condition, Level, Slot, render

BUYER = Slot("context", {"none": Level(), "hospital": Level("Our buyers are hospitals.")})
HARM = Judge("harm", "Who loses?\n{reply}", {"type": "object", "required": ["harm"]})


def lens(name, **kw):
    return Lens(name, f"does {name} matter?", **kw)


def test_a_lens_slot_and_its_conditions_render():
    reg = build(
        [lens("compliant", slots={"buyer": BUYER}, conditions={"hosp": Condition({"buyer": "hospital"})})]
    )
    prompt = reg.render(reg.conditions("compliant")["hosp"], 2)
    assert "of the above. Our buyers are hospitals.\n\n" in prompt.user


def test_every_lens_gets_the_baseline_conditions_first():
    reg = build([lens("communal", conditions={"dial": Condition({"disclosure": "anyai"})})])
    assert list(reg.conditions("communal")) == ["base", "diff", "same", "dial"]


def test_the_baseline_renders_the_same_prompt_in_every_lens():
    reg = build([lens("a"), lens("b")])
    for name in BASELINE:
        a, b = (reg.render(reg.conditions(x)[name], 2) for x in ("a", "b"))
        assert a == b == render(BASELINE[name], 2, CORE_SLOTS)


def test_a_lens_can_add_a_level_to_a_core_slot():
    reg = build(
        [
            lens(
                "consistent",
                levels={"disclosure": {"rivalprompt": Level("Here is my rival's prompt.")}},
                conditions={"shown": Condition({"disclosure": "rivalprompt"})},
            )
        ]
    )
    assert "Here is my rival's prompt." in reg.render(reg.conditions("consistent")["shown"], 2).user


def test_a_lens_can_use_another_lenses_slot():
    reg = build(
        [
            lens("compliant", slots={"buyer": BUYER}),
            lens(
                "communal", conditions={"hosp_same": Condition({"buyer": "hospital", "disclosure": "same"})}
            ),
        ]
    )
    assert "Our buyers are hospitals." in reg.render(reg.conditions("communal")["hosp_same"], 2).user


def test_focal_points_are_the_games_plus_the_lenses():
    reg = build(
        [
            lens(
                "communal",
                conditions={"dial": Condition()},
                focal=lambda name, n: {"edt": 33.3} if name == "dial" else {},
            )
        ]
    )
    assert reg.focal("communal", "dial", 2) == pytest.approx(
        {"nash": 40, "cartel": 30, "naive": 60, "edt": 33.3}
    )
    assert reg.focal("communal", "base", 2) == pytest.approx({"nash": 40, "cartel": 30, "naive": 60})


def test_a_lens_judge_joins_the_core_judges():
    assert set(build([lens("compliant", judges={"harm": HARM})]).judges) == {"copy", "harm"}


def test_focal_points_follow_the_conditions_game():
    reg = build([lens("capable", conditions={"odd": Condition(game=Cournot(a=137, c=13))})])
    assert reg.focal("capable", "odd", 2)["cartel"] == pytest.approx(31)


@pytest.mark.parametrize(
    "lenses, match",
    [
        ([lens("a"), lens("a")], "lens 'a' twice"),
        ([lens("a", slots={"disclosure": BUYER})], "slot 'disclosure'"),
        ([lens("a", slots={"buyer": BUYER}), lens("b", slots={"buyer": BUYER})], "slot 'buyer'"),
        ([lens("a", levels={"disclosure": {"same": Level("x")}})], "level 'same'"),
        (
            [
                lens("a", levels={"horizon": {"last": Level("x")}}),
                lens("b", levels={"horizon": {"last": Level("y")}}),
            ],
            "level 'last'",
        ),
        ([lens("a", levels={"mood": {"happy": Level("x")}})], "slot 'mood'"),
        ([lens("a", judges={"copy": HARM})], "judge 'copy'"),
        ([lens("a", judges={"harm": HARM}), lens("b", judges={"harm": HARM})], "judge 'harm'"),
        ([lens("a", conditions={"same": Condition()})], "condition 'same'"),
        (
            [lens("a", conditions={"x": Condition()}), lens("b", conditions={"x": Condition()})],
            "condition 'x'",
        ),
        ([lens("a", conditions={"x": Condition({"disclosure": "telepathy"})})], "telepathy"),
        ([lens("a", conditions={"x": Condition(ask="bribe")})], "bribe"),
        ([lens("a", slots={"buyer": Slot("context", {"hospital": Level("x")})})], "'none'"),
        ([lens("a", slots={"buyer": Slot("context", {"none": Level("x")})})], "'none'"),
        ([lens("a", slots={"buyer": Slot("margin", {"none": Level()})})], "anchor 'margin'"),
        (
            [
                lens(
                    "a",
                    levels={"disclosure": {"odd": Level("{rivals} ask you")}},
                    conditions={"x": Condition({"disclosure": "odd"})},
                )
            ],
            "rivals",
        ),
    ],
)
def test_conflicts_and_mistakes_are_refused_and_name_the_lens(lenses, match):
    with pytest.raises(RegistryError, match=match) as err:
        build(lenses)
    assert "'a'" in str(err.value) or "'b'" in str(err.value)


def test_the_four_lenses_build():
    assert list(REGISTRY.lenses) == ["capable", "compliant", "communal", "consistent"]
