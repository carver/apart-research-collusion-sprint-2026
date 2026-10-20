import pytest

from tradingcartel.core import record


@pytest.fixture(autouse=True)
def logs_dir(tmp_path, monkeypatch):
    """Every test's run logs go to a temporary folder, never the project's logs/."""
    folder = tmp_path / "logs"
    monkeypatch.setattr(record, "LOGS_DIR", folder)
    return folder
