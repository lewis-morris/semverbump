import json
import os
import subprocess
import sys
from pathlib import Path

from cli_helpers import run, setup_repo


def _setup_cli_repo(tmp_path: Path, enable_in_config: bool = False) -> tuple[Path, str, str]:
    """Create a repository with a CLI command that is later removed."""
    repo, pkg, _ = setup_repo(tmp_path)
    if enable_in_config:
        (repo / "bumpwright.toml").write_text(
            """[project]\npublic_roots=['pkg']\n[analysers]\ncli = true\n""",
            encoding="utf-8",
        )
        run(["git", "add", "bumpwright.toml"], repo)
    (pkg / "cli.py").write_text(
        """import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
p_run = sub.add_parser('run')
""",
        encoding="utf-8",
    )
    run(["git", "add", "pkg/cli.py"], repo)
    run(["git", "commit", "-m", "add cli"], repo)
    base = run(["git", "rev-parse", "HEAD"], repo)
    (pkg / "cli.py").write_text(
        """import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
""",
        encoding="utf-8",
    )
    run(["git", "add", "pkg/cli.py"], repo)
    run(["git", "commit", "-m", "drop cli"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo)
    return repo, base, head


def test_enable_analyser_flag(tmp_path: Path) -> None:
    """CLI flag enables an analyser not set in configuration."""
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
            "--enable-analyser",
            "cli",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    data = json.loads(res.stderr)
    assert data["level"] == "major"
    assert data["confidence"] == 1.0
    assert data["reasons"] == ["Removed command"]


def test_disable_analyser_flag(tmp_path: Path) -> None:
    """CLI flag disables an analyser configured in the project."""
    repo, base, head = _setup_cli_repo(tmp_path, enable_in_config=True)
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
            "--disable-analyser",
            "cli",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    data = json.loads(res.stderr)
    assert data["level"] is None
    assert data["confidence"] == 0.0
    assert data["reasons"] == []
