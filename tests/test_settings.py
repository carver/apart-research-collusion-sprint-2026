import sys
from dataclasses import dataclass, fields
from typing import ClassVar

import pytest

from tradingcartel.experiments.settings import RunSettings


def log_for(monkeypatch, *flags: str):
    monkeypatch.setattr(sys, "argv", ["run", *flags])
    return RunSettings.from_command_line("test", "exp")[1]


def test_a_test_model_run_writes_no_log_unless_asked(monkeypatch):
    assert log_for(monkeypatch) is None
    assert log_for(monkeypatch, "--write") is not None


@pytest.mark.parametrize(("flags", "logged"), [((), True), (("--no-write",), False)])
def test_a_real_model_run_writes_a_log_unless_told_not_to(monkeypatch, flags, logged):
    assert (log_for(monkeypatch, "--model", "claude-cli:haiku", *flags) is not None) is logged


@dataclass(frozen=True)
class Versioned(RunSettings):
    VERSION: ClassVar[int | None] = 3
    seed: int = 0


def test_an_experiments_version_goes_in_the_log_header_but_isnt_a_setting():
    assert Versioned().log_header()["version"] == 3
    assert "version" not in RunSettings().log_header()
    assert "VERSION" not in [field.name for field in fields(Versioned)]
