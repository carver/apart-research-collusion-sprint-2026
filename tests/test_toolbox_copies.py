"""The copies of llm-toolbox tools in bin/ and lib/ are listed twice: in REUSE.toml's table that
credits Jason alone, and in ruff's extend-exclude, which keeps the pre-commit hook's ruff format from
rewriting a copy away from its original. The two lists must match, but for the copies REUSE.toml
credits to both authors."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Toolbox copies that hold Thomas's changes too, so REUSE.toml's code table covers them.
JOINT_COPIES = {"bin/session-digest"}


def reuse_copies() -> set[str]:
    """bin/ and lib/ paths that REUSE.toml licenses as Jason's alone, with `lib/**` as `lib`."""
    annotations = tomllib.loads((ROOT / "REUSE.toml").read_text())["annotations"]
    return {
        path.removesuffix("/**")
        for entry in annotations
        if entry["SPDX-FileCopyrightText"] == "2026 Jason Carver"
        and entry["SPDX-License-Identifier"] == "MIT"
        for path in ([entry["path"]] if isinstance(entry["path"], str) else entry["path"])
        if path.startswith(("bin/", "lib/"))
    }


def ruff_excluded() -> set[str]:
    return set(tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["ruff"]["extend-exclude"])


def test_every_toolbox_copy_is_kept_from_ruff_and_nothing_else_is():
    assert reuse_copies() | JOINT_COPIES == ruff_excluded()
