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
    """Parse the settings from the command line, run the experiment with a log (or none, see
    ``RunSettings.from_command_line``), and pass what ``run`` returns to ``report`` to print. Then
    finish the log and print the usage totals and where the log is. The log goes under the name of
    the experiment's folder, the one holding ``experiment_file``."""
    experiment = Path(experiment_file).parent.name
    settings, run_log = settings_type.from_command_line(description, experiment)
    report(asyncio.run(run(settings, run_log)))
    if run_log:
        run_log.finish()
        print(f"\n{run_log.describe_totals()}\n\nLog: {run_log.path}")
