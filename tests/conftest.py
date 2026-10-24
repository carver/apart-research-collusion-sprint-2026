"""Every test runs without the GIT_* variables a git hook or `git rebase --exec` exports. With GIT_DIR set, a
test's `git init` in a temporary folder re-initialises the repo GIT_DIR names, marking it bare, and the test's
commits land in that repo: a `git rebase --exec` of the tests in a worktree did this to the main checkout."""

import os

import pytest


@pytest.fixture(autouse=True)
def no_git_variables(monkeypatch):
    for name in [name for name in os.environ if name.startswith("GIT_")]:
        monkeypatch.delenv(name)
