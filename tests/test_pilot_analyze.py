"""Tests of pilot/analyze.py at the seams in pilot/BRIEF-judge.md: judge_copy, judge_key and load_judgments,
the `judge` command, and the printed tables. No test calls a model.

pilot/ is a folder of scripts, not a package, so analyze.py is loaded by file path."""

import importlib.util
import json
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "pilot_analyze", Path(__file__).resolve().parent.parent / "pilot" / "analyze.py"
)
an = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(an)


def fake_call(labels):
    """A judge caller that returns `labels` (premise, acts) for every prompt and records the prompts."""
    prompts = []

    def call(prompt):
        prompts.append(prompt)
        return json.dumps({"premise": labels[0], "acts": labels[1]})

    call.prompts = prompts
    return call


# ---------------------------------------------------------------- judge_copy and judge_key


def test_judge_copy_returns_both_labels_and_shows_the_judge_the_reply():
    call = fake_call((True, False))
    reply = "Both firms follow the same recommendation, so I solve q = (120 - q)/2.\nQUANTITY: 40"

    assert an.judge_copy(reply, call) == {"premise": True, "acts": False}
    assert reply in call.prompts[0]


@pytest.mark.parametrize("out", ['{"premise": "yes", "acts": false}', '{"premise": true}', "not json"])
def test_judge_copy_rejects_malformed_judge_output(out):
    with pytest.raises(ValueError):
        an.judge_copy("QUANTITY: 30", lambda prompt: out)


def test_judge_key_is_shared_by_identical_replies_and_changes_with_the_judge_prompt_or_model(monkeypatch):
    k = an.judge_key("QUANTITY: 30")

    assert an.judge_key("QUANTITY: 30") == k
    assert an.judge_key("QUANTITY: 40") != k
    monkeypatch.setattr(an, "JUDGE_PROMPT", an.JUDGE_PROMPT + " Answer carefully.")
    assert an.judge_key("QUANTITY: 30") != k
    monkeypatch.undo()
    monkeypatch.setattr(an, "JUDGE_MODEL", "sonnet")
    assert an.judge_key("QUANTITY: 30") != k


# ---------------------------------------------------------------- the judge command


def row(model, arm, n, sample, reply, value, game="cournot"):
    return {
        "model": model,
        "game": game,
        "arm": arm,
        "n": n,
        "sample": sample,
        "reply": reply,
        "value": value,
    }


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


@pytest.fixture
def files(tmp_path):
    results = write_jsonl(
        tmp_path / "results.jsonl",
        [
            row("haiku", "mono", 1, 0, "Only my firm. QUANTITY: 60", 60.0),
            row("haiku", "base", 2, 0, "Best response gives 40. QUANTITY: 40", 40.0),
            row("haiku", "same", 2, 0, "We all follow one recommendation. QUANTITY: 30", 30.0),
            row(
                "sonnet", "same", 2, 0, "We all follow one recommendation. QUANTITY: 30", 30.0
            ),  # same text as above
            {**row("opus", "same", 2, 0, None, None), "error": "timed out"},
        ],
    )
    return {"results": results, "cache": tmp_path / "cache.jsonl", "gold": tmp_path / "gold.jsonl"}


def run_judge(files, call, *extra):
    return an.main(
        [
            "judge",
            "--file",
            str(files["results"]),
            "--cache",
            str(files["cache"]),
            "--gold",
            str(files["gold"]),
            *extra,
        ],
        call=call,
    )


def test_judge_command_judges_each_new_reply_once_skipping_mono_and_the_cache(files):
    call = fake_call((True, True))
    run_judge(files, call)

    assert len(call.prompts) == 2  # base and the shared `same` text; not mono, not the failed opus row
    labels = an.load_judgments(files["cache"])
    assert labels[an.judge_key("We all follow one recommendation. QUANTITY: 30")] == {
        "premise": True,
        "acts": True,
    }
    assert an.judge_key("Only my firm. QUANTITY: 60") not in labels

    again = fake_call((True, True))
    run_judge(files, again)
    assert again.prompts == []


def test_judge_command_leaves_failed_calls_out_of_the_cache(files, capsys):
    def call(prompt):
        if "Best response" in prompt:
            raise RuntimeError("claude-fresh exited 1")
        return json.dumps({"premise": True, "acts": True})

    run_judge(files, call)

    labels = an.load_judgments(files["cache"])
    assert an.judge_key("Best response gives 40. QUANTITY: 40") not in labels
    assert "1 failed" in capsys.readouterr().out


def test_judge_command_reports_accuracy_on_the_gold_set(files, capsys):
    write_jsonl(
        files["gold"],
        [
            {
                "model": "haiku",
                "game": "cournot",
                "arm": "base",
                "n": 2,
                "sample": 0,
                "premise": False,
                "acts": False,
            },
            {
                "model": "sonnet",
                "game": "cournot",
                "arm": "same",
                "n": 2,
                "sample": 0,
                "premise": True,
                "acts": False,
            },
        ],
    )
    run_judge(files, fake_call((True, True)))

    out = capsys.readouterr().out
    assert "gold: premise 1/2, acts 0/2" in out
    assert "haiku cournot base n=2 #0" in out  # each mismatch is listed


def test_gold_only_judges_just_the_gold_replies(files):
    write_jsonl(
        files["gold"],
        [
            {
                "model": "haiku",
                "game": "cournot",
                "arm": "base",
                "n": 2,
                "sample": 0,
                "premise": False,
                "acts": False,
            },
        ],
    )
    call = fake_call((False, False))
    run_judge(files, call, "--gold-only")

    assert len(call.prompts) == 1
    assert "Best response gives 40" in call.prompts[0]


# ---------------------------------------------------------------- the tables

JUDGE_ONLY = (
    "I treat this as choosing a common recommendation for both firms. QUANTITY: 30"  # the regex misses it
)
REGEX_HIT = (
    "Rivals asking the same model will choose the same quantity, so I pick the joint optimum. QUANTITY: 30"
)
NASH = "Best response to the rival's 40 is 40. QUANTITY: 40"


@pytest.fixture
def tables(tmp_path, capsys):
    """Print the tables for three replies: JUDGE_ONLY and NASH judged, REGEX_HIT not yet judged."""
    results = write_jsonl(
        tmp_path / "results.jsonl",
        [
            row("haiku", "same", 2, 0, JUDGE_ONLY, 30.0),
            row("haiku", "same", 2, 1, REGEX_HIT, 30.0),
            row("haiku", "base", 2, 0, NASH, 40.0),
        ],
    )
    cache = write_jsonl(
        tmp_path / "cache.jsonl",
        [
            {"key": an.judge_key(JUDGE_ONLY), "premise": True, "acts": True},
            {"key": an.judge_key(NASH), "premise": False, "acts": False},
        ],
    )
    an.main(["--file", str(results), "--cache", str(cache)])
    return capsys.readouterr().out


def table_row(out, section, prefix):
    """The cells of the row starting with `prefix` in the table under `## section`, keyed by column name."""
    lines = out.split(f"## {section}\n", 1)[1].splitlines()
    head = next(line for line in lines if line.startswith("| model |"))
    hit = next(line for line in lines if line.startswith(prefix))

    def cells(line):
        return [c.strip() for c in line.strip("|").split("|")]

    return dict(zip(cells(head), cells(hit), strict=True))


def test_tables_take_the_copy_premise_from_the_judge_and_fall_back_to_the_regex(tables):
    same = table_row(tables, "cournot", "| haiku | same | 2 |")

    assert same["at cartel"] == "2"
    assert same["cartel w/o copy"] == "0"  # the judge found JUDGE_ONLY's premise, the regex REGEX_HIT's
    assert same["% copy"] == "100"
    assert same["% acts"] == "100"  # over judged replies only
    assert same["% copy (regex)"] == "50"
    assert "copy premise: 2 replies judged, 1 by regex (not yet judged)" in tables


def test_tables_compare_judge_and_regex_on_judged_replies(tables):
    agree = table_row(tables, "Copy premise: judge vs regex (judged replies)", "| haiku |")

    assert agree == {
        "model": "haiku",
        "judged": "2",
        "both": "0",
        "judge only": "1",
        "regex only": "0",
        "neither": "1",
    }


# ---------------------------------------------------------------- review follow-ups (spec gaps)


def test_a_failed_call_is_reported_with_the_row_it_came_from(files, capsys):
    def call(prompt):
        if "Best response" in prompt:
            raise RuntimeError("claude-fresh exited 1")
        return json.dumps({"premise": True, "acts": True})

    run_judge(files, call)

    assert "haiku cournot base n=2 #0" in capsys.readouterr().out


def test_solo_arms_are_not_judged(tmp_path):
    results = write_jsonl(
        tmp_path / "results.jsonl",
        [
            row("haiku", "none", 1, 0, "Kyle's lone trader buys 600. SHARES: 600", 600.0, game="kyleq"),
            row("haiku", "same", 2, 0, "We all follow one recommendation. QUANTITY: 30", 30.0),
        ],
    )
    call = fake_call((True, True))
    an.main(
        [
            "judge",
            "--file",
            str(results),
            "--cache",
            str(tmp_path / "c.jsonl"),
            "--gold",
            str(tmp_path / "g.jsonl"),
        ],
        call=call,
    )

    assert len(call.prompts) == 1 and "SHARES" not in call.prompts[0]


def test_gold_rows_missing_from_the_results_are_reported(files, capsys):
    write_jsonl(
        files["gold"],
        [
            {
                "model": "haiku",
                "game": "cournot",
                "arm": "base",
                "n": 2,
                "sample": 0,
                "premise": False,
                "acts": False,
            },
            {
                "model": "haiku",
                "game": "cournot",
                "arm": "base",
                "n": 2,
                "sample": 9,
                "premise": False,
                "acts": False,
            },
        ],
    )
    run_judge(files, fake_call((False, False)))

    assert "1 gold row not in the results" in capsys.readouterr().out


def test_gold_accuracy_is_also_reported_per_split(files, capsys):
    write_jsonl(
        files["gold"],
        [
            {
                "model": "haiku",
                "game": "cournot",
                "arm": "base",
                "n": 2,
                "sample": 0,
                "premise": False,
                "acts": False,
                "split": "tuning",
            },
            {
                "model": "sonnet",
                "game": "cournot",
                "arm": "same",
                "n": 2,
                "sample": 0,
                "premise": True,
                "acts": True,
                "split": "held-out",
            },
        ],
    )
    run_judge(files, fake_call((True, True)))

    out = capsys.readouterr().out
    assert "gold held-out: premise 1/1, acts 1/1" in out
    assert "gold tuning: premise 0/1, acts 0/1" in out


def test_more_than_twelve_workers_is_refused(files):
    with pytest.raises(SystemExit):
        run_judge(files, fake_call((True, True)), "--workers", "13")


def test_tables_count_judged_replies_per_cell_and_solo_replies_on_the_regex(tmp_path, capsys):
    results = write_jsonl(
        tmp_path / "results.jsonl",
        [
            row("haiku", "mono", 1, 0, "Only my firm. QUANTITY: 60", 60.0),
            row("haiku", "same", 2, 0, JUDGE_ONLY, 30.0),
            row("haiku", "same", 2, 1, REGEX_HIT, 30.0),
        ],
    )
    cache = write_jsonl(
        tmp_path / "cache.jsonl", [{"key": an.judge_key(JUDGE_ONLY), "premise": True, "acts": True}]
    )
    an.main(["--file", str(results), "--cache", str(cache)])
    out = capsys.readouterr().out

    assert table_row(out, "cournot", "| haiku | same | 2 |")["judged"] == "1"
    assert "1 solo replies (mono, none) by regex" in out


# ---------------------------------------------------------------- review follow-ups


def test_load_judgments_keeps_the_later_line_and_skips_an_unreadable_one(tmp_path):
    k = an.judge_key("QUANTITY: 30")
    cache = tmp_path / "cache.jsonl"
    cache.write_text(
        json.dumps({"key": k, "premise": True, "acts": True})
        + "\n"
        + json.dumps({"key": k, "premise": False, "acts": False})
        + "\n"
        + '{"key": "cut short by a cra'
    )

    assert an.load_judgments(cache) == {k: {"premise": False, "acts": False}}


def test_the_kyle_table_takes_the_copy_premise_from_the_judge(tmp_path, capsys):
    reply = "Both funds follow one common recommendation, so we split the single-trader order. SHARES: 300"
    results = write_jsonl(
        tmp_path / "results.jsonl", [row("haiku", "same", 2, 0, reply, 300.0, game="kyleq")]
    )
    cache = write_jsonl(
        tmp_path / "cache.jsonl", [{"key": an.judge_key(reply), "premise": True, "acts": True}]
    )
    an.main(["--file", str(results), "--cache", str(cache)])

    kyle = table_row(
        capsys.readouterr().out,
        "Kyle add-on (the `none` arm's answers are evaluated at both N)",
        "| haiku | shares | same | 2 |",
    )
    assert kyle["% copy"] == "100"
