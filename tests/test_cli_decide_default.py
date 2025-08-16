import json
import os
import subprocess
import sys
from pathlib import Path

from cli_helpers import run, setup_repo


def test_decide_flag_defaults_to_previous_commit(tmp_path: Path) -> None:
    repo, pkg, _ = setup_repo(tmp_path)

    (pkg / "extra.py").write_text("def bar() -> int:\n    return 2\n", encoding="utf-8")
    run(["git", "add", "pkg/extra.py"], repo)
    run(["git", "commit", "-m", "feat: add bar"], repo)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "bumpwright.cli",
            "bump",
            "--decide",
            "--format",
            "json",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )

    data = json.loads(res.stderr)
    assert data["level"] == "minor"
    assert data["confidence"] == 1.0
    assert data["reasons"] == ["Added public symbol"]
