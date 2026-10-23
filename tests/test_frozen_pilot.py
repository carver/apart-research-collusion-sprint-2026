"""Tests of bin/pilot-lock, the pre-commit check that keeps the pre-sprint pilot frozen.
Each test builds a throwaway git repo and runs the check in it."""

import os
import subprocess
from pathlib import Path

import pytest

LOCK = Path(__file__).resolve().parent.parent / "bin" / "pilot-lock"


def clean_env(**extra):
    """The environment without git's own variables, which a hook sets for the repo being committed."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "PILOT_UNLOCK"} | extra


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=clean_env())


@pytest.fixture
def repo(tmp_path):
    for path in (
        "pilot/probe.py",
        "logs/pilot/probe-results.jsonl",
        "tests/test_pilot_probe.py",
        "README.md",
    ):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("frozen\n")
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", ".")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "pilot", "--no-verify")
    return tmp_path


def check(repo, unlock=False):
    env = clean_env(PILOT_UNLOCK="1") if unlock else clean_env()
    return subprocess.run([str(LOCK)], cwd=repo, env=env, capture_output=True, text=True)


@pytest.mark.parametrize(
    "path", ["pilot/probe.py", "logs/pilot/probe-results.jsonl", "tests/test_pilot_probe.py"]
)
def test_a_staged_change_to_the_pilot_is_refused_and_named(repo, path):
    (repo / path).write_text("changed\n")
    git(repo, "add", path)
    r = check(repo)
    assert r.returncode == 1
    assert path in r.stderr


def test_a_new_file_under_pilot_is_refused(repo):
    (repo / "pilot" / "new.py").write_text("x = 1\n")
    git(repo, "add", "pilot/new.py")
    assert check(repo).returncode == 1


def test_deleting_a_pilot_file_is_refused(repo):
    git(repo, "rm", "-q", "pilot/probe.py")
    assert check(repo).returncode == 1


def test_changes_elsewhere_pass(repo):
    (repo / "README.md").write_text("changed\n")
    git(repo, "add", "README.md")
    assert check(repo).returncode == 0


def test_unstaged_pilot_edits_pass(repo):
    (repo / "pilot" / "probe.py").write_text("changed\n")
    assert check(repo).returncode == 0


def test_pilot_unlock_lets_a_pilot_change_through(repo):
    (repo / "pilot" / "probe.py").write_text("changed\n")
    git(repo, "add", "pilot/probe.py")
    assert check(repo, unlock=True).returncode == 0


@pytest.fixture
def hook_git_env(tmp_path_factory, monkeypatch):
    """git's environment in a pre-commit hook run from a linked worktree, or by `git commit -a`: GIT_DIR and
    GIT_INDEX_FILE name the repo being committed. Here they name a decoy, whose index must not change."""
    decoy = tmp_path_factory.mktemp("decoy")
    subprocess.run(["git", "init", "-q", str(decoy)], check=True)
    (decoy / "kept.txt").write_text("kept\n")
    subprocess.run(["git", "-C", str(decoy), "add", "kept.txt"], check=True)
    index = decoy / ".git" / "index"
    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(index))
    return index, index.read_bytes()


def test_the_hooks_git_environment_stays_out_of_the_throwaway_repo(hook_git_env, repo):
    index, before = hook_git_env
    (repo / "pilot" / "probe.py").write_text("changed\n")
    git(repo, "add", "pilot/probe.py")
    assert check(repo).returncode == 1
    assert index.read_bytes() == before
