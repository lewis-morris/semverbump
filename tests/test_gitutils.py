import shlex
import subprocess
from pathlib import Path

import pytest

from semverbump.gitutils import _run, read_file_at_ref


def test_run_raises_called_process_error() -> None:
    cmd = ["python", "-c", "import sys; sys.exit(3)"]
    with pytest.raises(subprocess.CalledProcessError) as exc:
        _run(cmd)
    assert exc.value.returncode == 3
    assert exc.value.cmd == shlex.join(cmd)


def test_read_file_at_ref_missing(tmp_path: Path) -> None:
    repo = tmp_path
    _run(["git", "init"], str(repo))
    _run(["git", "config", "user.email", "a@b.c"], str(repo))
    _run(["git", "config", "user.name", "tester"], str(repo))
    _run(["git", "commit", "--allow-empty", "-m", "init"], str(repo))
    head = _run(["git", "rev-parse", "HEAD"], str(repo)).strip()
    assert read_file_at_ref(head, "missing.txt", cwd=str(repo)) is None
