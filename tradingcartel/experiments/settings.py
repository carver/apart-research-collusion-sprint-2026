"""What an experiment run takes, and the command-line flags that set it. An experiment with more
settings subclasses ``RunSettings``, adding fields and their flags."""

import argparse
from dataclasses import asdict, dataclass, fields
from typing import Any, Self, get_args

from pydantic_ai.models import Model

from tradingcartel.agents.llm import ReasoningEffort
from tradingcartel.core.record import RunLog


@dataclass(frozen=True)
class RunSettings:
    """``max_messages`` stops the run after that many messages, a cost brake."""

    model: str | Model = "test"
    max_messages: int = 100
    reasoning_effort: ReasoningEffort | None = None

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """Add a flag for each setting, defaulting to the field's default, and ``--no-write``."""
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
        parser.add_argument(
            "--no-write", action="store_true", help="don't write a log to logs/ or count usage"
        )

    @classmethod
    def from_command_line(cls, description: str, experiment: str) -> tuple[Self, RunLog | None]:
        """The settings the command line gives, and the run's log under logs/``experiment``/, or
        None with ``--no-write``."""
        parser = argparse.ArgumentParser(
            description=description, formatter_class=argparse.RawDescriptionHelpFormatter
        )
        cls.add_arguments(parser)
        args = parser.parse_args()
        settings = cls(**{field.name: getattr(args, field.name) for field in fields(cls)})
        return settings, None if args.no_write else RunLog(experiment, **settings.log_header())

    def log_header(self) -> dict[str, Any]:
        """The settings, for the first line of the run's log, with the model by name."""
        model = self.model if isinstance(self.model, str) else self.model.model_name
        return asdict(self) | {"model": model}
