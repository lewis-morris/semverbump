from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, List, Set

from bumpwright import gitutils


def _legacy_list_py_files_at_ref(
    ref: str,
    roots: Iterable[str],
    ignore_globs: Iterable[str] | None = None,
    cwd: str | None = None,
) -> Set[str]:
    """Legacy helper to mirror previous list-based implementation."""
    out = gitutils._run(["git", "ls-tree", "-r", "--name-only", ref], cwd)
    paths: List[str] = []
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
