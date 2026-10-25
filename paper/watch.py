"""bin/build-paper watch: rebuilds the draft whenever the repo's HEAD moves."""

import argparse
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

from paper.git import Repo


def watch(head: Callable[[], str], rebuild: Callable[[str], None], wait: Callable[[], None]) -> NoReturn:
    """Builds for the commit `head()` names, then again each time it names another; `wait()` between polls."""
    built = ""
    while True:
        commit = head()
        if commit and commit != built:
            built = commit
            rebuild(commit)
        else:
            wait()


def rebuild_draft(repo: Repo, commit: str) -> None:
    """One draft build in a fresh process, so a commit that changes the paper's code takes effect."""
    subject = repo.git("log", "-1", "--format=%s", commit).stdout.strip()
    print(f"\n=== {time.strftime('%H:%M:%S')} HEAD {commit[:7]} {subject}: building", flush=True)
    code = subprocess.run([sys.executable, "-m", "paper"], cwd=repo.root).returncode
    if code:
        print(f"=== build failed (exit {code}); still watching", flush=True)


def main(argv: list[str], paper_dir: Path) -> int:
    parser = argparse.ArgumentParser(
        prog="build-paper watch",
        description="Build the draft now, then again each time the repo's HEAD moves (a commit, checkout, "
        "merge or rebase). A move during a build brings one more build after it. Ctrl-C stops it.",
    )
    parser.add_argument(
        "--interval", type=float, default=2.0, metavar="SECONDS", help="how often to read HEAD (default 2)"
    )
    args = parser.parse_args(argv)
    repo = Repo.of(paper_dir)
    if repo is None:
        print(f"build-paper watch: {paper_dir} is not in a git repository", file=sys.stderr)
        return 1
    try:
        watch(repo.head, lambda commit: rebuild_draft(repo, commit), lambda: time.sleep(args.interval))
    except KeyboardInterrupt:
        return 0
