from __future__ import annotations

from bumpwright import gitutils
from bumpwright.analyzers.utils import iter_py_files_at_ref


def test_iter_py_files_at_ref(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    pkg = repo / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("a = 1\n")
    (pkg / "mod.py").write_text("b = 2\n")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "."], str(repo))
    gitutils._run(["git", "commit", "-m", "init"], str(repo))

    files = dict(iter_py_files_at_ref("HEAD", ["pkg"], [], str(repo)))
    assert files["pkg/__init__.py"] == "a = 1\n"
    assert files["pkg/mod.py"] == "b = 2\n"

    files = dict(iter_py_files_at_ref("HEAD", ["pkg"], ["pkg/mod.py"], str(repo)))
    assert set(files) == {"pkg/__init__.py"}
