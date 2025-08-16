from __future__ import annotations

import ast

from bumpwright import gitutils
from bumpwright.analysers import utils
from bumpwright.analysers.utils import _is_const_str, iter_py_files_at_ref


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


def test_is_const_str() -> None:
    const_node = ast.parse("'foo'").body[0].value  # type: ignore[assignment]
    other_node = ast.parse("1").body[0].value  # type: ignore[assignment]
    assert _is_const_str(const_node)
    assert not _is_const_str(other_node)


def test_iter_py_files_at_ref_single_git_call(monkeypatch):
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_read_files_at_ref(ref: str, paths: list[str], cwd: str | None = None):
        calls.append((ref, tuple(paths)))
        return {p: f"{p}-contents" for p in paths}

    def fake_list_py_files_at_ref(
        ref: str,
        roots: list[str],
        ignore_globs: list[str] | None = None,
        cwd: str | None = None,
    ) -> set[str]:
        return {"a.py", "b.py"}

    monkeypatch.setattr(utils, "read_files_at_ref", fake_read_files_at_ref)
    monkeypatch.setattr(utils, "list_py_files_at_ref", fake_list_py_files_at_ref)

    files = dict(iter_py_files_at_ref("HEAD", ["."], []))

    assert files == {"a.py": "a.py-contents", "b.py": "b.py-contents"}
    assert len(calls) == 1
