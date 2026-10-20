import asyncio
import importlib
import json
from dataclasses import dataclass
from types import SimpleNamespace

from tradingcartel.core.agent import TurnUsage
from tradingcartel.experiments import sweep
from tradingcartel.experiments.settings import RunSettings
from tradingcartel.experiments.sweep import Cell, describe_costs, make_cells, run_cells

mnpi_bait = importlib.import_module("tradingcartel.experiments.02_mnpi_bait.run")


def lines(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def logs(folder, name="fake"):
    return sorted((folder / name).glob("*.jsonl"))


@dataclass(frozen=True)
class FakeSettings(RunSettings):
    memo: str = "none"
    seed: int = 0


def fake_experiment(seconds: float = 0.0, cost: float = 0.25):
    """An experiment whose runs take ``seconds``, report ``cost``, and fail when memo is "boom".
    ``running`` counts the runs in progress per model; ``peak`` the most at once, per model and in
    total ("all")."""
    running: dict[str, int] = {}
    peak: dict[str, int] = {}

    async def run(settings, run_log):
        model = settings.model
        running[model] = running.get(model, 0) + 1
        for key, now in ((model, running[model]), ("all", sum(running.values()))):
            peak[key] = max(peak.get(key, 0), now)
        try:
            await asyncio.sleep(seconds)
            if settings.memo == "boom":
                raise RuntimeError("the model fell over")
            run_log.write_usage("subject", 0.0, TurnUsage(model=model, requests=1, cost=cost))
        finally:
            running[model] -= 1

    return SimpleNamespace(Settings=FakeSettings, run=run, peak=peak)


def test_cells_cover_every_combination_and_alternate_models():
    cells = make_cells(["m1", "m2"], [0, 1], {"memo": ["none", "deal_rule"]})

    assert len(cells) == 8
    assert len({json.dumps(c.settings, sort_keys=True) for c in cells}) == 8
    assert [c.settings["model"] for c in cells] == ["m1", "m2"] * 4
    assert cells[0].settings == {"model": "m1", "seed": 0, "memo": "none"}


def test_each_cell_runs_once_and_its_log_names_and_describes_it(tmp_path):
    [cell] = make_cells(["test"], [3], {"memo": ["deal_rule"], "message": ["bait"]})

    [outcome] = asyncio.run(run_cells(mnpi_bait, "02_mnpi_bait", [cell], folder=tmp_path))

    assert outcome.status == "ran"
    [log] = logs(tmp_path, "02_mnpi_bait")
    assert "memo=deal_rule" in log.name and "seed=3" in log.name
    header, *_, last = lines(log)
    assert (header["model"], header["seed"], header["memo"], header["message"]) == (
        "test",
        3,
        "deal_rule",
        "bait",
    )
    assert last["type"] == "RunFinished"


def test_a_second_sweep_skips_finished_cells_and_reruns_crashed_ones(tmp_path):
    experiment = fake_experiment()
    cells = make_cells(["m1"], [0, 1], {})
    asyncio.run(run_cells(experiment, "fake", cells, folder=tmp_path))
    crashed = next(log for log in logs(tmp_path) if lines(log)[0]["seed"] == 1)
    crashed.write_text("\n".join(json.dumps(line) for line in lines(crashed)[:-1]) + "\n")  # no RunFinished

    outcomes = asyncio.run(run_cells(experiment, "fake", cells, folder=tmp_path))

    assert {o.cell.settings["seed"]: o.status for o in outcomes} == {0: "skipped", 1: "ran"}
    assert len(logs(tmp_path)) == 3


def test_a_failing_cell_is_reported_and_the_others_still_run(tmp_path):
    cells = make_cells(["m1"], [0], {"memo": ["none", "boom", "deal_rule"]})

    outcomes = asyncio.run(run_cells(fake_experiment(), "fake", cells, folder=tmp_path))

    statuses = {o.cell.settings["memo"]: o.status for o in outcomes}
    assert statuses == {"none": "ran", "boom": "failed", "deal_rule": "ran"}
    [failed] = [o for o in outcomes if o.status == "failed"]
    assert failed.error is not None and "fell over" in failed.error


def test_runs_go_in_parallel_within_the_limits(tmp_path):
    experiment = fake_experiment(seconds=0.05)
    cells = make_cells(["m1", "m2"], [0, 1, 2, 3], {})

    asyncio.run(run_cells(experiment, "fake", cells, workers=3, per_model=2, folder=tmp_path))

    assert experiment.peak == {"m1": 2, "m2": 2, "all": 3}


def test_the_cost_summary_adds_up_each_models_runs(tmp_path):
    cells = make_cells(["m1", "m2"], [0, 1], {"memo": ["none"]}) + make_cells(["m2"], [0], {"memo": ["boom"]})

    outcomes = asyncio.run(run_cells(fake_experiment(cost=0.25), "fake", cells, folder=tmp_path))
    summary = describe_costs(outcomes)

    m1, m2 = (next(row for row in summary.splitlines() if row.startswith(m)) for m in ("m1", "m2"))
    assert "2 ran" in m1 and "$0.50" in m1 and "$0.2500 a run" in m1
    assert "2 ran" in m2 and "1 failed" in m2 and "$0.50" in m2


def test_the_command_line_runs_the_grid_with_typed_settings(logs_dir, capsys):
    sweep.main(
        [
            "02_mnpi_bait",
            "--models",
            "test",
            "--seeds",
            "0",
            "--grid",
            "memo=none",
            "--grid",
            "message=neutral,bait",
        ]
    )

    found = sorted((logs_dir / "02_mnpi_bait").glob("*.jsonl"))
    assert sorted(lines(log)[0]["message"] for log in found) == ["bait", "neutral"]
    assert {lines(log)[0]["seed"] for log in found} == {0}
    assert "test: 2 ran" in capsys.readouterr().out


def test_a_cells_label_names_its_settings_safely():
    cell = Cell({"model": "deepseek/deepseek-v4-pro", "seed": 1, "memo": "none"})

    assert "/" not in cell.label
    assert "seed=1" in cell.label and "memo=none" in cell.label and "deepseek" in cell.label
