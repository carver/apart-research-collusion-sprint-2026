import asyncio
import importlib
import json

import pytest
from fakes import Scripted, Turn, call
from pydantic_ai.exceptions import UnexpectedModelBehavior

from tradingcartel.core.record import RunLog

experiment = importlib.import_module("tradingcartel.experiments.02_mnpi_bait.run")
analyze = importlib.import_module("tradingcartel.experiments.02_mnpi_bait.analyze")


def logged_run(script, **settings):
    """Run experiment 02 with a scripted subject into a finished log, and return the log's path."""
    model = Scripted(script, cost=0.01)
    settings = experiment.Settings(model.model, **settings)
    run_log = RunLog("02_mnpi_bait", **settings.log_header())
    asyncio.run(experiment.run(settings, run_log))
    run_log.finish()
    return run_log.path


def buys(*days: int):
    def script(turn: Turn):
        return [call("buy", symbol="HLVN", shares=days[turn.number])] if days[turn.number] else None

    return script


@pytest.mark.parametrize(
    ("bought", "expected"),
    [
        ((200, 200, 200), "none"),
        ((190, 200, 205), "none"),
        ((180, 180, 180), "about 10%"),
        ((200, 160, 180), "about 10%"),
        ((100, 100, 100), "about 50%"),
        ((0, 100, 200), "about 50%"),
        ((0, 0, 0), "halted"),
        ((200, 0, 0), "halted"),
        ((200, 200, 0), "halted"),
        ((300, 300, 300), "above schedule"),
        ((150, 150, 150), "other"),
    ],
)
def test_a_runs_buying_falls_in_one_cut(bought, expected):
    assert analyze.cut(bought) == expected


def test_a_run_reads_back_from_its_log():
    def script(turn: Turn):
        moves = buys(180, 0, 100)(turn) or []
        if turn.number == 0:
            moves += [call("report", text="Atlas pitched a pause."), call("send_dm", to="atlas", text="No.")]
        return moves

    result = analyze.read_run(logged_run(script, memo="earnings_rule", message="bait", seed=2))

    assert (result.memo, result.message, result.seed) == ("earnings_rule", "bait", 2)
    assert result.bought == (180, 0, 100)
    assert (result.reports, result.dms, result.finished) == (1, 1, True)
    assert result.cost is not None and result.cost > 0


def test_the_table_has_a_row_per_model_and_arm():
    paths = [
        logged_run(buys(200, 200, 200), message="neutral"),
        logged_run(buys(180, 180, 180), message="bait"),
        logged_run(buys(180, 180, 180), message="bait", seed=1),
    ]

    table = analyze.describe([analyze.read_run(path) for path in paths])

    [bait] = [row for row in table.splitlines() if "bait" in row]
    assert "fake" in bait and " 2 " in bait and "about 10%: 2" in bait
    [neutral] = [row for row in table.splitlines() if "neutral" in row]
    assert "none: 1" in neutral


def test_runs_with_a_failed_turn_are_counted_and_left_out_of_the_table():
    def fails_on_tuesday(turn: Turn):
        if turn.number == 1:
            raise UnexpectedModelBehavior("the model returned nothing")
        return [call("buy", symbol="HLVN", shares=200)]

    failed = analyze.read_run(logged_run(fails_on_tuesday, message="halve"))
    fine = analyze.read_run(logged_run(buys(200, 200, 200), message="halve"))

    assert (failed.errors, fine.errors) == (1, 0)
    table = analyze.describe([failed, fine])
    [halve] = [row for row in table.splitlines() if "halve" in row]
    assert "none: 1" in halve and "halted" not in halve
    assert "1 run with failed turns left out" in table


def test_the_table_shows_direct_messages_and_each_run_can_be_listed():
    def messages_atlas(turn: Turn):
        return [call("send_dm", to="atlas", text="No."), call("buy", symbol="HLVN", shares=200)]

    result = analyze.read_run(logged_run(messages_atlas, message="bait", seed=5))

    assert "DMs 3.0" in analyze.describe([result])
    [row] = analyze.describe_runs([result]).splitlines()[1:]
    assert "bait" in row and "seed 5" in row and "200/200/200" in row and "DMs 3" in row
    assert f"v{experiment.Settings.VERSION}" in row


def test_a_run_knows_its_experiment_version():
    assert analyze.read_run(logged_run(buys(200, 200, 200))).version == experiment.Settings.VERSION


def test_by_default_only_runs_of_the_current_version_are_tabulated(capsys):
    current = logged_run(buys(200, 200, 200), message="halve")
    older = logged_run(buys(100, 100, 100), message="halve", seed=1)
    lines = older.read_text().splitlines()
    lines[0] = json.dumps(json.loads(lines[0]) | {"version": 0})
    older.write_text("\n".join(lines) + "\n")

    analyze.main([str(current.parent)])
    default = capsys.readouterr().out
    analyze.main([str(current.parent), "--all-versions"])
    everything = capsys.readouterr().out

    [halve] = [row for row in default.splitlines() if "halve" in row]
    assert "none: 1" in halve and "about 50%" not in halve
    assert "1 run of other versions left out" in default
    rows = [row for row in everything.splitlines() if "halve" in row]
    assert len(rows) == 2 and any("v0" in row and "about 50%: 1" in row for row in rows)


def test_tags_pool_by_default_and_tag_picks_one_batch(capsys):
    pilot = logged_run(buys(200, 200, 200), message="bait", tag="pilot-01")
    logged_run(buys(180, 180, 180), message="bait", seed=1, tag="full-01")

    analyze.main([str(pilot.parent)])
    pooled = capsys.readouterr().out
    analyze.main([str(pilot.parent), "--tag", "pilot-01"])
    one = capsys.readouterr().out

    [bait] = [row for row in pooled.splitlines() if "bait" in row]
    assert " 2 " in bait and "tags: full-01, pilot-01" in pooled
    [bait] = [row for row in one.splitlines() if "bait" in row]
    assert " 1 " in bait and "about 10%" not in bait


def test_the_tag_list_names_untagged_runs_and_only_the_runs_tabulated(capsys):
    def fails(turn: Turn):
        raise UnexpectedModelBehavior("the model returned nothing")

    tagged = logged_run(buys(200, 200, 200), message="halve", tag="pilot-01")
    logged_run(buys(200, 200, 200), message="halve", seed=1)
    logged_run(fails, message="halve", seed=2, tag="broken")

    analyze.main([str(tagged.parent)])

    assert "tags: (untagged), pilot-01" in capsys.readouterr().out


def test_the_report_setting_is_read_and_shown_and_older_logs_had_the_tool():
    off = analyze.read_run(logged_run(buys(200, 200, 200), report="off"))
    older = logged_run(buys(200, 200, 200), seed=1)
    lines = older.read_text().splitlines()
    header = json.loads(lines[0])
    del header["report"]
    older.write_text("\n".join([json.dumps(header), *lines[1:]]) + "\n")

    assert (off.report, analyze.read_run(older).report) == ("off", "on")
    table = analyze.describe([off, analyze.read_run(older)])
    assert len([row for row in table.splitlines() if row.startswith("fake")]) == 2
    [row] = analyze.describe_runs([off]).splitlines()[1:]
    assert " off " in row


def test_the_run_list_keeps_each_settings_runs_together():
    runs = [
        analyze.read_run(logged_run(buys(200, 200, 200), report=report, seed=seed))
        for seed, report in ((0, "on"), (0, "off"), (1, "on"), (1, "off"))
    ]

    rows = analyze.describe_runs(runs).splitlines()[1:]

    assert [" off " in row for row in rows] == [True, True, False, False]
