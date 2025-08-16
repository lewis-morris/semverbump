import os
import subprocess
from pathlib import Path

from bumpwright.cli.decide import _build_api_at_ref


def _run(cmd: list[str], cwd: Path) -> str:
    res = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return res.stdout.strip()


def test_build_api_respects_ignores(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init"], repo)
    _run(["git", "config", "user.email", "a@b.c"], repo)
    _run(["git", "config", "user.name", "tester"], repo)

    pkg = repo / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "included.py").write_text("def foo() -> int:\n    return 1\n")
    (pkg / "ignored.py").write_text("def bar() -> int:\n    return 2\n")

    _run(["git", "add", "pkg"], repo)
    _run(["git", "commit", "-m", "init"], repo)
    ref = _run(["git", "rev-parse", "HEAD"], repo)

    old_cwd = os.getcwd()
    os.chdir(repo)
    try:
        api = _build_api_at_ref(ref, ["pkg"], ["pkg/ignored.py"], ["_"])
    finally:
        os.chdir(old_cwd)

    assert "included:foo" in api
    assert "ignored:bar" not in api
