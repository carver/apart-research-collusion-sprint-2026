"""bin/agent-pre-commit, in a throwaway repo, with a stand-in for uv whose three checks (reuse, pytest and
pyright) each wait until all three have started."""

import contextlib
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "bin" / "agent-pre-commit"
CHECKS = ("reuse", "pytest", "pyright")
# A stand-in for uv. `uv run --no-sync -q TOOL ...` prints "TOOL: started", writes its pid to $MARKS/TOOL,
# waits up to 10 s for every check to have started, prints "TOOL: done", and fails when TOOL is in $FAILING.
# With $HANG set, it then becomes a process that sleeps for a minute instead. Every other uv command passes.
FAKE_UV = """#!/bin/sh
[ "$1" = run ] || exit 0
shift
while case $1 in -*) true ;; *) false ;; esac; do shift; done
tool=$1
echo "$tool: started"
echo $$ > "$MARKS/$tool"
tries=0
until [ -e "$MARKS/reuse" ] && [ -e "$MARKS/pytest" ] && [ -e "$MARKS/pyright" ]; do
  tries=$((tries + 1))
  if [ $tries -gt 200 ]; then echo "$tool: the other checks never started"; exit 1; fi
  sleep 0.05
done
[ -n "${HANG:-}" ] && exec sleep 60
echo "$tool: done"
case " ${FAILING:-} " in *" $tool "*) echo "$tool: FAILED"; exit 1 ;; esac
exit 0
"""


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "bin").mkdir(parents=True)
    shutil.copy(SCRIPT, repo / "bin" / "agent-pre-commit")
    (repo / "notes.md").write_text("a note\n")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    fake = tmp_path / "fakebin"
    fake.mkdir()
    (fake / "uv").write_text(FAKE_UV)
    (fake / "uv").chmod(0o755)
    (tmp_path / "marks").mkdir()
    return repo


def environment(repo: Path, **extra: str) -> dict[str, str]:
    return os.environ | {
        "PATH": f"{repo.parent / 'fakebin'}{os.pathsep}{os.environ['PATH']}",
        "MARKS": str(repo.parent / "marks"),
        **extra,
    }


def run(repo: Path, failing: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(repo / "bin" / "agent-pre-commit")],
        cwd=repo,
        env=environment(repo, FAILING=failing),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
    )


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def test_the_three_checks_run_at_once_and_pass(repo):
    result = run(repo)
    assert result.returncode == 0, result.stdout
    for check in CHECKS:
        assert f"{check}: done" in result.stdout


def test_each_checks_output_stays_in_one_piece(repo):
    lines = run(repo).stdout.splitlines()
    for check in CHECKS:
        started = lines.index(f"{check}: started")
        assert lines[started + 1] == f"{check}: done"


@pytest.mark.parametrize("sent", [signal.SIGINT, signal.SIGTERM, signal.SIGHUP])
def test_an_interrupted_hook_leaves_no_check_running(repo, sent):
    """Ctrl-C reaches the hook's whole process group; a closed terminal or a kill reaches the hook alone."""
    hook = subprocess.Popen(
        [str(repo / "bin" / "agent-pre-commit")],
        cwd=repo,
        env=environment(repo, HANG="1"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    marks = repo.parent / "marks"
    pids = {}
    for _ in range(200):  # until every check has written its pid, or 10 s
        pids = {check: (marks / check).read_text().strip() for check in CHECKS if (marks / check).exists()}
        if len(pids) == len(CHECKS) and all(pids.values()):
            break
        time.sleep(0.05)
    try:
        time.sleep(0.2)  # every check is past its rendezvous and asleep
        if sent == signal.SIGINT:
            os.killpg(hook.pid, sent)
        else:
            os.kill(hook.pid, sent)
            os.kill(int(pids["pytest"]), sent)  # sh runs its trap only once the foreground check ends
        assert hook.wait(timeout=10) != 0
        time.sleep(0.2)
        assert [check for check, pid in pids.items() if alive(int(pid))] == []
    finally:
        for pid in pids.values():
            with contextlib.suppress(ProcessLookupError):
                os.kill(int(pid), signal.SIGKILL)


@pytest.mark.parametrize("check", CHECKS)
def test_a_failing_check_fails_the_hook_and_shows_its_output(repo, check):
    result = run(repo, failing=check)
    assert result.returncode != 0
    assert f"{check}: FAILED" in result.stdout
