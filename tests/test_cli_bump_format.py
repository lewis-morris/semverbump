import json
import os
import subprocess
import sys
from pathlib import Path

from tests.test_cli_auto import _setup_repo


def test_bump_command_json_format(tmp_path: Path) -> None:
    """Ensure bump emits machine-readable JSON when requested."""
    repo, _, _ = _setup_repo(tmp_path)
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "bumpwright.cli",
            "bump",
            "--level",
            "minor",
            "--pyproject",
            "pyproject.toml",
            "--dry-run",
            "--format",
            "json",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    data = json.loads(res.stdout)
    assert data["old_version"] == "0.1.0"
    assert data["new_version"] == "0.2.0"
    assert data["level"] == "minor"
