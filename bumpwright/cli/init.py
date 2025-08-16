"""Initialisation command for the bumpwright CLI."""

from __future__ import annotations

import argparse
import subprocess

from ..gitutils import last_release_commit


def init_command(_args: argparse.Namespace) -> int:
    """Create an empty baseline release commit.

    This establishes a starting point for future semantic version bumps. The
    function is idempotent: if a baseline already exists, no new commit is
    created.

    Args:
        _args: Parsed command-line arguments. Present for API compatibility but
            currently unused.

    Returns:
        Exit status code. ``0`` indicates success or that the baseline was
        already present, while ``1`` indicates an error.
    """

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
