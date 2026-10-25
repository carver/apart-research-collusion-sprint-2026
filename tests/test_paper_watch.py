"""bin/build-paper watch, through `watch` with a scripted HEAD and no real build: it builds at the start and
after each move, once for moves that land mid-build, and never for an unreadable HEAD."""

import subprocess

import pytest

from paper.__main__ import main
from paper.git import Repo
from paper.watch import watch


class Stop(Exception):
    pass


def run(heads_per_poll: list[str], heads_after_build: dict[int, str] | None = None) -> list[str]:
    """The commits `watch` builds while HEAD reads `heads_per_poll` in turn, one per poll; a build numbered
    in `heads_after_build` moves HEAD to its commit while that build runs."""
    polls = iter(heads_per_poll)
    current = next(polls)
    built: list[str] = []

    def rebuild(commit: str) -> None:
        nonlocal current
        built.append(commit)
        if heads_after_build and len(built) in heads_after_build:
            current = heads_after_build[len(built)]

    def wait() -> None:
        nonlocal current
        try:
            current = next(polls)
        except StopIteration:  # the script has run out: stop watching
            raise Stop from None

    with pytest.raises(Stop):
        watch(lambda: current, rebuild, wait)
    return built


def test_it_builds_at_the_start_and_after_each_move():
    assert run(["a", "a", "b", "b", "b", "c", "a"]) == ["a", "b", "c", "a"]


def test_a_move_during_a_build_brings_one_more_build_right_after():
    assert run(["a", "c", "c"], heads_after_build={1: "b"}) == ["a", "b", "c"]


def test_an_unreadable_head_builds_nothing():
    assert run(["", "a", "", "a", "b"]) == ["a", "b"]


def test_a_repo_with_no_commit_yet_reads_as_no_head(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    repo = Repo.of(tmp_path)
    assert repo is not None
    assert repo.head() == ""


def test_watch_outside_a_repo_fails_with_why(tmp_path, capsys):
    assert main(["watch"], tmp_path) == 1
    assert "not in a git repository" in capsys.readouterr().err
