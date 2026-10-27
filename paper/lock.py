"""The build lock: a build of a paper holds <build dir>/.lock, so a second build of it waits instead of
clearing the first one's figures mid-compile. It imports nothing heavy, so a process that only takes the
lock starts fast."""

import fcntl
import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

__all__ = ["build_lock", "lock_holder"]

LOCK = ".lock"  # in build/: held by the build that is running, with its pid inside


@contextmanager
def build_lock(out: Path) -> Iterator[None]:
    """Holds <out>/.lock for a build, after waiting for any other build of the same paper to finish. The OS
    drops the lock when its process ends, so a crashed build leaves none behind."""
    out.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(out / LOCK, os.O_RDWR | os.O_CREAT, 0o644), "r+") as lock:
        if not _try_lock(lock):
            pid = _read_pid(lock)
            holder = f"pid {pid}" if pid else "pid unknown"
            print(f"build-paper: waiting for another build of this paper ({holder})", file=sys.stderr)
            fcntl.flock(lock, fcntl.LOCK_EX)
        lock.seek(0)
        lock.truncate()
        lock.write(str(os.getpid()))
        lock.flush()
        yield


def lock_holder(out: Path) -> int | None:
    """The pid of the process holding <out>/.lock, or None when no build runs (or, for an instant, when the
    one that just took it hasn't written its pid yet)."""
    if not (out / LOCK).exists():
        return None
    with (out / LOCK).open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return _read_pid(lock)
        fcntl.flock(lock, fcntl.LOCK_UN)
        return None


def _try_lock(lock: IO[str]) -> bool:
    """Takes the lock if it is free. Tries a few times over 50 ms, since lock_holder() takes it for an
    instant to see whether it is free."""
    for _ in range(5):
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            time.sleep(0.01)
    return False


def _read_pid(lock: IO[str]) -> int | None:
    lock.seek(0)
    text = lock.read().strip()
    return int(text) if text.isdigit() else None
