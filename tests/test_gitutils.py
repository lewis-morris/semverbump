from __future__ import annotations

import subprocess
from collections.abc import Iterable
from fnmatch import fnmatch
from pathlib import Path
from unittest.mock import Mock

import pytest

from bumpwright import gitutils
from bumpwright.cli.decide import _infer_base_ref


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

    assert _infer_base_ref() == "origin/main"


def test_infer_base_ref_without_upstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback to ``origin/HEAD`` when no upstream is set."""

    def _raise(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        raise subprocess.CalledProcessError(1, "git rev-parse")

    monkeypatch.setattr(subprocess, "run", Mock(side_effect=_raise))

    assert _infer_base_ref() == "origin/HEAD"


def test_run_success_and_failure() -> None:
    """Ensure ``_run`` returns output and raises on errors."""

    out = gitutils._run(["git", "--version"])
    assert "git version" in out

    with pytest.raises(subprocess.CalledProcessError):
        gitutils._run(["git", "definitely-not-a-command"])


def test_changed_paths(tmp_path: Path) -> None:
    """Detect changed files between two commits and invalid refs."""

    repo = tmp_path / "repo"
    repo.mkdir()
    file = repo / "file.txt"
    file.write_text("one\n", encoding="utf-8")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "file.txt"], str(repo))
    gitutils._run(["git", "commit", "-m", "first"], str(repo))
    file.write_text("two\n", encoding="utf-8")
    gitutils._run(["git", "commit", "-am", "second"], str(repo))
    changed = gitutils.changed_paths("HEAD^", "HEAD", str(repo))
    assert changed == {"file.txt"}

    with pytest.raises(subprocess.CalledProcessError):
        gitutils.changed_paths("BAD", "HEAD", str(repo))


def test_read_file_at_ref(tmp_path: Path) -> None:
    """Read file contents at a ref and handle missing paths."""

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "file.txt").write_text("hello\n", encoding="utf-8")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "file.txt"], str(repo))
    gitutils._run(["git", "commit", "-m", "first"], str(repo))
    content = gitutils.read_file_at_ref("HEAD", "file.txt", str(repo))
    assert content == "hello\n"
    assert gitutils.read_file_at_ref("HEAD", "missing.txt", str(repo)) is None


def test_read_file_at_ref_caches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cache file reads at refs to avoid redundant git calls."""

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "file.txt").write_text("hello\n", encoding="utf-8")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "file.txt"], str(repo))
    gitutils._run(["git", "commit", "-m", "first"], str(repo))

    gitutils.read_file_at_ref.cache_clear()
    original = subprocess.run
    calls: list[list[str]] = []

    def spy(cmd: list[str], *args, **kwargs) -> subprocess.CompletedProcess:
        if isinstance(cmd, list) and cmd[:3] == ["git", "cat-file", "--batch"]:
            calls.append(cmd)
        return original(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    gitutils.read_file_at_ref("HEAD", "file.txt", str(repo))
    gitutils.read_file_at_ref("HEAD", "file.txt", str(repo))
    assert calls and calls[0][:3] == ["git", "cat-file", "--batch"]
    assert len(calls) == 1
    gitutils.read_file_at_ref.cache_clear()


def test_last_release_commit_found(tmp_path: Path) -> None:
    """Return the hash of the latest release commit."""

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "file.txt").write_text("hi\n", encoding="utf-8")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "file.txt"], str(repo))
    gitutils._run(["git", "commit", "-m", "chore(release): 1.0.0"], str(repo))
    head = gitutils._run(["git", "rev-parse", "HEAD"], str(repo)).strip()
    assert gitutils.last_release_commit(str(repo)) == head

def test_read_files_at_ref(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Read multiple file contents and handle missing paths."""

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "file1.txt").write_text("one\n", encoding="utf-8")
    (repo / "file2.txt").write_text("two\n", encoding="utf-8")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "."], str(repo))
    gitutils._run(["git", "commit", "-m", "first"], str(repo))

    contents = gitutils.read_files_at_ref("HEAD", ["file1.txt", "file2.txt"], str(repo))
    assert contents == {"file1.txt": "one\n", "file2.txt": "two\n"}

    missing = gitutils.read_files_at_ref(
        "HEAD", ["file1.txt", "missing.txt"], str(repo)
    )
    assert missing["file1.txt"] == "one\n"
    assert missing["missing.txt"] is None

    def fake_run(cmd: list[str], *args, **kwargs) -> subprocess.CompletedProcess:
        if cmd[:3] == ["git", "cat-file", "--batch"]:
            return subprocess.CompletedProcess(cmd, 1, b"", b"bad ref")
        return subprocess.CompletedProcess(cmd, 0, b"", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(subprocess.CalledProcessError):
        gitutils.read_files_at_ref("BAD", ["file1.txt"], str(repo))


def test_read_files_at_ref_caches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cache multiple file reads to avoid redundant git calls."""

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "file1.txt").write_text("one\n", encoding="utf-8")
    (repo / "file2.txt").write_text("two\n", encoding="utf-8")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "."], str(repo))
    gitutils._run(["git", "commit", "-m", "first"], str(repo))

    gitutils.read_files_at_ref.cache_clear()
    original = subprocess.run
    calls: list[list[str]] = []

    def spy(cmd: list[str], *args, **kwargs) -> subprocess.CompletedProcess:
        if isinstance(cmd, list) and cmd[:3] == ["git", "cat-file", "--batch"]:
            calls.append(cmd)
        return original(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    gitutils.read_files_at_ref("HEAD", ["file1.txt", "file2.txt"], str(repo))
    gitutils.read_files_at_ref("HEAD", ["file1.txt", "file2.txt"], str(repo))
    assert calls and calls[0][:3] == ["git", "cat-file", "--batch"]
    assert len(calls) == 1
    gitutils.read_files_at_ref.cache_clear()


def test_last_release_commit_none(tmp_path: Path) -> None:
    """Return ``None`` when no release commit exists."""

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "file.txt").write_text("hi\n", encoding="utf-8")
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "file.txt"], str(repo))
    gitutils._run(["git", "commit", "-m", "feat: initial"], str(repo))
    assert gitutils.last_release_commit(str(repo)) is None
