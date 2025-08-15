import os
import subprocess
import sys
from pathlib import Path

from semverbump.versioning import read_project_version


def _run(cmd: list[str], cwd: Path) -> str:
    res = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return res.stdout.strip()


def _setup_repo(tmp_path: Path) -> tuple[Path, Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init"], repo)
    _run(["git", "config", "user.email", "a@b.c"], repo)
    _run(["git", "config", "user.name", "tester"], repo)

    (repo / "pyproject.toml").write_text(
        """
[project]
name = "demo"
version = "0.1.0"
""",
        encoding="utf-8",
    )

    pkg = repo / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        "def foo() -> int:\n    return 1\n", encoding="utf-8"
    )
    (repo / "semverbump.toml").write_text(
        "[project]\npublic_roots=['pkg']\n", encoding="utf-8"
    )
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-m", "base"], repo)
    base = _run(["git", "rev-parse", "HEAD"], repo)
    return repo, pkg, base


def test_auto_command_bumps_version(tmp_path: Path) -> None:
    repo, pkg, base = _setup_repo(tmp_path)

    (pkg / "extra.py").write_text("def bar() -> int:\n    return 2\n", encoding="utf-8")
    _run(["git", "add", "pkg/extra.py"], repo)
    _run(["git", "commit", "-m", "feat: add bar"], repo)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "semverbump.cli",
            "auto",
            "--base",
            base,
            "--head",
            "HEAD",
            "--pyproject",
            "pyproject.toml",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )

    assert "Bumped version: 0.1.0 -> 0.2.0 (minor)" in res.stdout
    assert read_project_version(repo / "pyproject.toml") == "0.2.0"


def test_auto_command_dry_run(tmp_path: Path) -> None:
    repo, pkg, base = _setup_repo(tmp_path)

    (pkg / "extra.py").write_text("def bar() -> int:\n    return 2\n", encoding="utf-8")
    _run(["git", "add", "pkg/extra.py"], repo)
    _run(["git", "commit", "-m", "feat: add bar"], repo)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "semverbump.cli",
            "auto",
            "--base",
            base,
            "--head",
            "HEAD",
            "--pyproject",
            "pyproject.toml",
            "--dry-run",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )

    assert "Bumped version: 0.1.0 -> 0.2.0 (minor)" in res.stdout
    assert read_project_version(repo / "pyproject.toml") == "0.1.0"


def test_main_shows_help_when_no_args(tmp_path: Path) -> None:
    res = subprocess.run(
        [sys.executable, "-m", "semverbump.cli"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    assert "usage: semverbump" in res.stdout


def test_bump_command_searches_pyproject(tmp_path: Path) -> None:
    repo, pkg, _ = _setup_repo(tmp_path)
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "semverbump.cli",
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
