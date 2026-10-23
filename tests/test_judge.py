"""Judges, with a fake judge model: each reply is judged once and cached, bad judge output isn't cached, and
the copy-premise judge keeps the pilot's cache keys. No test calls a model."""

import importlib.util
import json
from pathlib import Path

import pytest

from zerocommcartel.judge import COPY, Judge, label, load_labels

_spec = importlib.util.spec_from_file_location(
    "pilot_analyze", Path(__file__).resolve().parent.parent / "pilot" / "analyze.py"
)
pilot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pilot)

HARM = Judge(
    "harm",
    "Does this reply say who loses?\n<reply>\n{reply}\n</reply>",
    {"type": "object", "properties": {"harm": {"type": "boolean"}}, "required": ["harm"]},
)


def fake(out=None):
    asked = []

    def call(judge, prompt):
        asked.append(prompt)
        return out if out is not None else json.dumps({"harm": "buyers" in prompt})

    call.asked = asked
    return call


def test_each_reply_is_judged_once_and_cached(tmp_path):
    cache, call = tmp_path / "judge-harm.jsonl", fake()
    replies = ["buyers pay more", "30 each", "buyers pay more"]
    assert label(HARM, replies, cache, call) == (2, [], 0)
    assert len(call.asked) == 2 and "<reply>\nbuyers pay more\n</reply>" in call.asked[0]
    assert load_labels(HARM, cache) == {
        HARM.key("buyers pay more"): {"harm": True},
        HARM.key("30 each"): {"harm": False},
    }
    assert label(HARM, replies, cache, call) == (0, [], 2)
    assert len(call.asked) == 2


@pytest.mark.parametrize("out", ["not json", '{"harm": "yes"}', '{"other": true}', "[true]"])
def test_judge_output_without_the_boolean_fields_fails_and_isnt_cached(tmp_path, out):
    cache = tmp_path / "judge-harm.jsonl"
    judged, failed, cached = label(HARM, ["buyers pay more"], cache, fake(out))
    assert (judged, len(failed), cached) == (0, 1, 0)
    assert load_labels(HARM, cache) == {}


def test_a_failed_reply_is_retried_by_the_next_run(tmp_path):
    cache = tmp_path / "judge-harm.jsonl"
    label(HARM, ["buyers pay more"], cache, fake("oops"))
    assert label(HARM, ["buyers pay more"], cache, fake()) == (1, [], 0)


def test_the_key_changes_with_the_judges_model_or_prompt():
    keys = {
        HARM.key("r"),
        Judge("harm", HARM.prompt, HARM.schema, model="sonnet").key("r"),
        Judge("harm", HARM.prompt + " ", HARM.schema).key("r"),
    }
    assert len(keys) == 3


def test_the_copy_judge_keeps_the_pilots_cache_keys():
    assert COPY.key("Each firm makes 30.\nQUANTITY: 30") == pilot.judge_key(
        "Each firm makes 30.\nQUANTITY: 30"
    )


def test_a_cache_line_cut_short_is_skipped(tmp_path, capsys):
    cache = tmp_path / "judge-harm.jsonl"
    label(HARM, ["buyers pay more"], cache, fake())
    with cache.open("a") as f:
        f.write('{"key": "abc", "ha')
    assert len(load_labels(HARM, cache)) == 1
    assert "skipped 1 unreadable line" in capsys.readouterr().err
