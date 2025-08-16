"""Tests for the CLI init command."""

import os
import subprocess
import sys
from pathlib import Path

from cli_helpers import run, setup_repo

from bumpwright.gitutils import last_release_commit


def test_init_creates_baseline_commit(tmp_path: Path) -> None:
    """Ensure the init command records a baseline release commit."""

    repo, _pkg, _base = setup_repo(tmp_path)
    subprocess.run(
        [sys.executable, "-m", "bumpwright.cli", "init"],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    msg = run(["git", "log", "-1", "--format=%s"], repo)
    assert msg == "chore(release): initialise baseline"
    head = run(["git", "rev-parse", "HEAD"], repo)
    assert last_release_commit(str(repo)) == head
