import os
import subprocess
import sys
from pathlib import Path

from cli_helpers import run, setup_repo

from bumpwright.versioning import read_project_version


def test_bump_command_searches_pyproject(tmp_path: Path) -> None:
    """Ensure bump locates pyproject.toml when run from a subdirectory."""
    repo, pkg, _ = setup_repo(tmp_path)
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "bumpwright.cli",
            "bump",
            "--level",
            "patch",
        ],
        cwd=pkg,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    assert "Bumped version: 0.1.0 -> 0.1.1 (patch)" in res.stdout
    assert read_project_version(repo / "pyproject.toml") == "0.1.1"


def test_bump_command_applies_changes(tmp_path: Path) -> None:
    """Apply a bump when relevant files have changed."""
    repo, pkg, base = setup_repo(tmp_path)
    (pkg / "extra.py").write_text("def bar() -> int:\n    return 2\n", encoding="utf-8")
    run(["git", "add", "pkg/extra.py"], repo)
    run(["git", "commit", "-m", "feat: add bar"], repo)
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    subprocess.run(
        [
            sys.executable,
            "-m",
            "bumpwright.cli",
            "bump",
            "--base",
            base,
            "--head",
            "HEAD",
            "--pyproject",
            "pyproject.toml",
            "--commit",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    assert read_project_version(repo / "pyproject.toml") == "0.2.0"


def test_main_shows_help_when_no_args(tmp_path: Path) -> None:
    """Running without arguments displays help text."""
    res = subprocess.run(
        [sys.executable, "-m", "bumpwright.cli"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    assert "usage: bumpwright" in res.stdout
