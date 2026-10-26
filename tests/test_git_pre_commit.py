"""bin/git-pre-commit, through real commits in a throwaway repo, with stand-ins for
bin/pilot-lock and uvx."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "bin" / "git-pre-commit"
# A stand-in for uvx. `pre-commit run` prints what the real one does on a pass, and fails when
# $PRE_COMMIT_FAILS is set; `ruff format` rewrites each file it's given when $RUFF_REFORMATS is
# set. Each call goes to $UVX_LOG, so a test can see whether it ran.
FAKE_UVX = """#!/bin/sh
echo "$*" >> "$UVX_LOG"
case "$*" in
  *pre-commit*)
    echo "ruff format..............................................................Passed"
    if [ -n "${PRE_COMMIT_FAILS:-}" ]; then echo "a.py:1:1: F401 unused import"; exit 1; fi ;;
  *ruff*format*)
    if [ -n "${RUFF_REFORMATS:-}" ]; then
      for file in "$@"; do case $file in *.py) echo "x = 1" > "$file" ;; esac; done
    fi ;;
esac
exit 0
"""


def git(repo, *args, env=None):
    return subprocess.run(["git", *args], cwd=repo, check=False, capture_output=True, text=True, env=env)


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "bin").mkdir(parents=True)
    shutil.copy(HOOK, repo / "bin" / "git-pre-commit")
    (repo / "bin" / "pilot-lock").write_text('#!/bin/sh\n[ -z "${PILOT_LOCKED:-}" ]\n')
    (repo / "bin" / "pilot-lock").chmod(0o755)
    fake = tmp_path / "fakebin"
    fake.mkdir()
    (fake / "uvx").write_text(FAKE_UVX)
    (fake / "uvx").chmod(0o755)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "t")
    git(repo, "config", "user.email", "t@example.com")
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(exist_ok=True)
    (hooks / "pre-commit").symlink_to("../../bin/git-pre-commit")
    (repo / ".pre-commit-config.yaml").write_text("repos: []\n")
    (repo / "notes.md").write_text("a note\n")
    git(repo, "add", ".")
    return repo


def commit(repo, **env):
    environ = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environ.pop("AI_AGENT", None)
    environ["PATH"] = f"{repo.parent / 'fakebin'}{os.pathsep}{environ['PATH']}"
    environ["UVX_LOG"] = str(repo.parent / "uvx.log")
    environ.update(env)
    return git(repo, "commit", "-q", "-m", "x", env=environ)


def uvx_calls(repo):
    log = repo.parent / "uvx.log"
    return log.read_text().splitlines() if log.exists() else []


def last_line(run):
    return run.stderr.rstrip().splitlines()[-1]


def test_a_passing_pre_commit_prints_nothing(repo):
    done = commit(repo)

    assert done.returncode == 0, done.stderr
    assert "Passed" not in done.stdout + done.stderr
    assert any("pre-commit" in call for call in uvx_calls(repo))


def test_a_failing_pre_commit_shows_its_output_and_ends_with_commit_refused(repo):
    done = commit(repo, PRE_COMMIT_FAILS="1")

    assert done.returncode != 0
    assert "F401" in done.stderr
    assert last_line(done).startswith("COMMIT REFUSED")


def test_an_unstaged_pre_commit_config_is_refused_before_pre_commit_runs(repo):
    (repo / ".pre-commit-config.yaml").write_text("repos: [changed]\n")

    done = commit(repo)

    assert done.returncode != 0
    assert ".pre-commit-config.yaml" in done.stderr and "stage" in done.stderr
    assert last_line(done).startswith("COMMIT REFUSED")
    assert not any("pre-commit" in call for call in uvx_calls(repo))


def test_a_pilot_lock_refusal_ends_with_commit_refused(repo):
    done = commit(repo, PILOT_LOCKED="1")

    assert done.returncode != 0 and last_line(done).startswith("COMMIT REFUSED")


def test_the_formatter_still_says_which_file_it_staged(repo):
    (repo / "a.py").write_text("x=1\n")
    git(repo, "add", "a.py")

    done = commit(repo, RUFF_REFORMATS="1")

    assert done.returncode == 0, done.stderr
    assert "ruff format changed a.py" in done.stderr
    assert git(repo, "show", "HEAD:a.py").stdout == "x = 1\n"
