from __future__ import annotations

import subprocess
from collections.abc import Iterable
from fnmatch import fnmatch
from pathlib import Path
from unittest.mock import Mock

import pytest

from bumpwright import cli, gitutils


def _legacy_list_py_files_at_ref(
    ref: str,
    roots: Iterable[str],
    ignore_globs: Iterable[str] | None = None,
    cwd: str | None = None,
) -> set[str]:
    """Legacy helper to mirror previous list-based implementation."""
    out = gitutils._run(["git", "ls-tree", "-r", "--name-only", ref], cwd)
    paths: list[str] = []
    roots_norm = [str(Path(r)) for r in roots]
    for line in out.splitlines():
        if not line.endswith(".py"):
            continue
        p = Path(line)
        if any(
            str(p).startswith(r.rstrip("/") + "/") or str(p) == r for r in roots_norm
        ):
            s = str(p)
            if ignore_globs and any(fnmatch(s, pat) for pat in ignore_globs):
                continue
            paths.append(s)
    return set(paths)


def test_list_py_files_at_ref_matches_legacy(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("\n")
    (repo / "pkg" / "ignored.py").write_text("\n")
    (repo / "root.py").write_text("\n")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "."], str(repo))
    gitutils._run(["git", "commit", "-m", "init"], str(repo))

    ignore = ["pkg/ignored.py"]
    expected = _legacy_list_py_files_at_ref("HEAD", ["."], ignore, str(repo))
    result = gitutils.list_py_files_at_ref("HEAD", ["."], ignore, str(repo))

    assert result == expected


def test_list_py_files_at_ref_caches(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("\n")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "."], str(repo))
    gitutils._run(["git", "commit", "-m", "init"], str(repo))

    gitutils.list_py_files_at_ref.cache_clear()
    original = gitutils._run
    calls: list[list[str]] = []

    def spy(cmd: list[str], cwd: str | None = None) -> str:
        if cmd[:3] == ["git", "ls-tree", "-r"]:
            calls.append(cmd)
        return original(cmd, cwd)

    monkeypatch.setattr(gitutils, "_run", spy)
    gitutils.list_py_files_at_ref("HEAD", ["."], cwd=str(repo))
    gitutils.list_py_files_at_ref("HEAD", ["."], cwd=str(repo))
    assert len(calls) == 1
    gitutils.list_py_files_at_ref.cache_clear()


def test_collect_commits(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    (repo / "file.txt").write_text("one\n", encoding="utf-8")
    gitutils._run(["git", "add", "file.txt"], str(repo))
    gitutils._run(["git", "commit", "-m", "first"], str(repo))
    (repo / "file.txt").write_text("two\n", encoding="utf-8")
    gitutils._run(["git", "commit", "-am", "second"], str(repo))
    sha = gitutils._run(["git", "rev-parse", "--short", "HEAD"], str(repo)).strip()
    commits = gitutils.collect_commits("HEAD^", "HEAD", str(repo))
    assert commits == [(sha, "second")]


def test_infer_base_ref_with_upstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the upstream branch when configured."""

    proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="origin/main\n")
    monkeypatch.setattr(subprocess, "run", Mock(return_value=proc))

    assert cli._infer_base_ref() == "origin/main"


def test_infer_base_ref_without_upstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback to ``origin/HEAD`` when no upstream is set."""

    def _raise(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        raise subprocess.CalledProcessError(1, "git rev-parse")

    monkeypatch.setattr(subprocess, "run", Mock(side_effect=_raise))

    assert cli._infer_base_ref() == "origin/HEAD"
