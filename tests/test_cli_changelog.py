import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from tests.cli_helpers import run, setup_repo


def test_bump_writes_changelog(tmp_path: Path) -> None:
    repo, pkg, _ = setup_repo(tmp_path)
    run(["git", "commit", "--allow-empty", "-m", "chore(release): 0.1.0"], repo)
    (pkg / "__init__.py").write_text(
        "def foo() -> int:\n    return 2\n", encoding="utf-8"
    )
    run(["git", "commit", "-am", "feat: change"], repo)
    sha = run(["git", "rev-parse", "--short", "HEAD"], repo)
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    subprocess.run(
        [
            sys.executable,
            "-m",
            "bumpwright.cli",
            "bump",
            "--level",
            "patch",
            "--pyproject",
            "pyproject.toml",
            "--dry-run",
            "--changelog",
            "CHANGELOG.md",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    content = (repo / "CHANGELOG.md").read_text()
    today = date.today().isoformat()
    assert f"## [v0.1.1] - {today}" in content
    assert f"- {sha} feat: change" in content
