import json
import os
import subprocess
import sys
from pathlib import Path

from tests.cli_helpers import run, setup_repo


def _setup_cli_repo(
    tmp_path: Path, enable_in_config: bool = False
) -> tuple[Path, str, str]:
    """Create a repository with a CLI command that is later removed."""
    repo, pkg, _ = setup_repo(tmp_path)
    if enable_in_config:
        (repo / "bumpwright.toml").write_text(
            """[project]\npublic_roots=['pkg']\n[analyzers]\ncli = true\n""",
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


def test_enable_analyzer_flag(tmp_path: Path) -> None:
    """CLI flag enables an analyzer not set in configuration."""
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
            "--enable-analyzer",
            "cli",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    data = json.loads(res.stdout)
    assert data["level"] == "major"


def test_disable_analyzer_flag(tmp_path: Path) -> None:
    """CLI flag disables an analyzer configured in the project."""
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
            "--disable-analyzer",
            "cli",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    data = json.loads(res.stdout)
    assert data["level"] is None
