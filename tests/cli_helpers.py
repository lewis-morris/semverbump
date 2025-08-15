import subprocess
from pathlib import Path
from typing import List, Tuple


def run(cmd: List[str], cwd: Path) -> str:
    """Execute a command and return its stdout.

    Args:
        cmd: Command and arguments.
        cwd: Working directory for the subprocess.

    Returns:
        Captured standard output stripped of trailing whitespace.
    """

    res = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return res.stdout.strip()


def setup_repo(tmp_path: Path) -> Tuple[Path, Path, str]:
    """Create a git repository with a minimal Python project.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        Tuple of repository path, package path, and base commit hash.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    run(["git", "init"], repo)
    run(["git", "config", "user.email", "a@b.c"], repo)
    run(["git", "config", "user.name", "tester"], repo)

    (repo / "pyproject.toml").write_text(
        """[project]\nname = 'demo'\nversion = '0.1.0'\n""",
        encoding="utf-8",
    )
    pkg = repo / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        "def foo() -> int:\n    return 1\n", encoding="utf-8"
    )
    (repo / "bumpwright.toml").write_text(
        "[project]\npublic_roots=['pkg']\n", encoding="utf-8"
    )
    run(["git", "add", "."], repo)
    run(["git", "commit", "-m", "base"], repo)
    base = run(["git", "rev-parse", "HEAD"], repo)
    return repo, pkg, base
