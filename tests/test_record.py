import json

from tradingcartel.core import record
from tradingcartel.core.agent import TurnUsage
from tradingcartel.core.messages import Notice
from tradingcartel.core.record import RunLog


def lines(run_log: RunLog) -> list[dict]:
    return [json.loads(line) for line in run_log.path.read_text().splitlines()]


def test_a_run_log_is_written_under_the_folder_it_is_given(tmp_path):
    run_log = RunLog("exp", folder=tmp_path, model="m", seed=1)

    assert run_log.path.parent == tmp_path / "exp"
    [header] = lines(run_log)
    assert (header["type"], header["experiment"]) == ("RunStarted", "exp")
    assert (header["model"], header["seed"]) == ("m", 1)
    assert "folder" not in header


def test_messages_then_the_totals_follow_the_header(tmp_path):
    run_log = RunLog("exp", folder=tmp_path)

    run_log.write(Notice(text="hello"))
    run_log.write_usage("alice", 5.0, TurnUsage(model="m", requests=1, input_tokens=10, cost=0.5))
    run_log.finish()

    header, notice, usage, finished = lines(run_log)
    assert [line["type"] for line in lines(run_log)] == ["RunStarted", "Notice", "TurnUsage", "RunFinished"]
    assert (usage["agent"], usage["time"], usage["input_tokens"], usage["cost"]) == ("alice", 5.0, 10, 0.5)
    assert finished["total"]["cost"] == 0.5


def test_tests_never_write_into_the_real_logs_folder():
    run_log = RunLog("exp")
    in_real_logs = run_log.path.is_relative_to(record.ROOT / "logs")
    if in_real_logs:
        run_log.path.unlink()
    assert not in_real_logs


def test_runs_started_in_the_same_second_get_separate_logs(tmp_path):
    first = RunLog("exp", folder=tmp_path, seed=1)
    second = RunLog("exp", folder=tmp_path, seed=2)

    assert first.path != second.path
    assert (lines(first)[0]["seed"], lines(second)[0]["seed"]) == (1, 2)


def test_a_label_names_the_log_file(tmp_path):
    run_log = RunLog("exp", folder=tmp_path, label="memo=none-seed=0")

    assert "memo=none-seed=0" in run_log.path.name
    assert "label" not in lines(run_log)[0]
