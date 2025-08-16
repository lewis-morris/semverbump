"""Tests for enabling and disabling analyzers via CLI flags."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tests.cli_helpers import run, setup_repo


def _setup_cli_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """Create a repository with CLI changes between two commits.

    The first commit contains a simple CLI command. The second commit adds an
    additional command so that the CLI analyzer would report a minor impact
    when enabled.

    Args:
        tmp_path: Temporary directory for the repository.

    Returns:
        Tuple of ``(repo_path, base_sha, head_sha)``.
    """

    repo, pkg, _ = setup_repo(tmp_path)
    cli_path = pkg / "cli.py"
    cli_path.write_text(
        """import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    p_cmd = sub.add_parser("cmd")
    return parser
""",
        encoding="utf-8",
    )
    run(["git", "add", "pkg/cli.py"], repo)
    run(["git", "commit", "-m", "add cli"], repo)
    base = run(["git", "rev-parse", "HEAD"], repo)

    cli_path.write_text(
        """import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    p_cmd = sub.add_parser("cmd")
    p_extra = sub.add_parser("extra")
    return parser
""",
        encoding="utf-8",
    )
    run(["git", "add", "pkg/cli.py"], repo)
    run(["git", "commit", "-m", "add extra command"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo)
    return repo, base, head


def test_enable_analyzer_flag(tmp_path: Path) -> None:
    """Enabling an analyzer via CLI flag activates it for the run."""

    repo, base, head = _setup_cli_repo(tmp_path)
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "bumpwright.cli",
            "bump",
            "--decide",
            "--base",
            base,
            "--head",
            head,
            "--format",
            "json",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    assert json.loads(res.stdout)["level"] is None

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "bumpwright.cli",
            "bump",
            "--decide",
            "--base",
            base,
            "--head",
            head,
            "--format",
            "json",
            "--enable-analyzer",
            "cli",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    assert json.loads(res.stdout)["level"] == "minor"


def test_disable_analyzer_flag(tmp_path: Path) -> None:
    """Disabling an analyzer via CLI flag overrides configuration settings."""

    repo, base, head = _setup_cli_repo(tmp_path)
    (repo / "bumpwright.toml").write_text(
        """[project]\npublic_roots=['pkg']\n[analyzers]\ncli = true\n""",
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "bumpwright.cli",
            "bump",
            "--decide",
            "--base",
            base,
            "--head",
            head,
            "--format",
            "json",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    assert json.loads(res.stdout)["level"] == "minor"

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "bumpwright.cli",
            "bump",
            "--decide",
            "--base",
            base,
            "--head",
            head,
            "--format",
            "json",
            "--disable-analyzer",
            "cli",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    assert json.loads(res.stdout)["level"] is None
