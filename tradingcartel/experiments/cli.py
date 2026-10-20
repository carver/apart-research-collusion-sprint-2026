"""Running an experiment from the command line, the same way for every experiment."""

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

from tradingcartel.core.record import RunLog
from tradingcartel.experiments.settings import RunSettings


def run_from_command_line[S: RunSettings, R](
    settings_type: type[S],
    description: str,
    experiment_file: str,
    run: Callable[[S, RunLog | None], Awaitable[R]],
    report: Callable[[R], None],
) -> None:
    """Run an experiment with the settings and log the command line asks for, print its
    ``report``, then the usage totals and the log's path. The log is named for the folder holding
    ``experiment_file``."""
    experiment = Path(experiment_file).parent.name
    settings, run_log = settings_type.from_command_line(description, experiment)
    report(asyncio.run(run(settings, run_log)))
    if run_log:
        run_log.finish()
        print(f"\n{run_log.describe_totals()}\n\nLog: {run_log.path}")
