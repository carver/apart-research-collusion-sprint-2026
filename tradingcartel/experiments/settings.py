"""What an experiment run takes, and the command-line flags that set it. An experiment with more
settings subclasses ``RunSettings``, adding fields and their flags."""

import argparse
from dataclasses import asdict, dataclass, fields
from typing import Any, Self, get_args

from pydantic_ai.models import Model

from tradingcartel.agents.llm import TEST_MODEL, ReasoningEffort
from tradingcartel.core.record import RunLog


@dataclass(frozen=True)
class RunSettings:
    """``max_messages`` stops the run after that many messages, a cost brake."""

    model: str | Model = TEST_MODEL
    max_messages: int = 100
    reasoning_effort: ReasoningEffort | None = None

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """Add a flag for each setting, defaulting to the field's default, and ``--write`` and
        ``--no-write``."""
        defaults = {field.name: field.default for field in fields(cls)}
        parser.add_argument(
            "--model",
            default=defaults["model"],
            help="an OpenRouter model id, claude-cli:<model>, or test (free, the default)",
        )
        parser.add_argument(
            "--max-messages", type=int, default=defaults["max_messages"], help="stop after this many messages"
        )
        parser.add_argument("--reasoning-effort", choices=get_args(ReasoningEffort), help="cap reasoning")
        writing = parser.add_mutually_exclusive_group()
        writing.add_argument(
            "--no-write", action="store_true", help="don't write a log to logs/ or count usage"
        )
        writing.add_argument(
            "--write", action="store_true", help="write a log even for the free test model, which skips it"
        )

    @classmethod
    def from_command_line(cls, description: str, experiment: str) -> tuple[Self, RunLog | None]:
        """The settings the command line gives, and the run's log under logs/``experiment``/, or
        None. A run writes a log unless told not to (``--no-write``), except a run with the free
        test model, which writes one only with ``--write``."""
        parser = argparse.ArgumentParser(
            description=description, formatter_class=argparse.RawDescriptionHelpFormatter
        )
        cls.add_arguments(parser)
        args = parser.parse_args()
        settings = cls(**{field.name: getattr(args, field.name) for field in fields(cls)})
        write = settings.model != TEST_MODEL
        if args.write or args.no_write:
            write = args.write
        return settings, RunLog(experiment, **settings.log_header()) if write else None

    def log_header(self) -> dict[str, Any]:
        """The settings, for the first line of the run's log, with the model by name."""
        model = self.model if isinstance(self.model, str) else self.model.model_name
        return asdict(self) | {"model": model}
