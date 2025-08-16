"""Initialisation command for the bumpwright CLI."""

from __future__ import annotations

import argparse
import subprocess

from ..gitutils import last_release_commit


def init_command(_args: argparse.Namespace) -> int:
    """Create an empty baseline release commit."""

    if last_release_commit() is not None:
        print("Baseline already initialised.")
        return 0

    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "chore(release): initialise baseline",
        ],
        check=True,
    )
    print("Created baseline release commit.")
    return 0
