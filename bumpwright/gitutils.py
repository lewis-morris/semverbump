"""Utility helpers for interacting with git repositories."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Iterable
from fnmatch import fnmatch
from functools import lru_cache
from io import BytesIO
from pathlib import Path


def _run(cmd: list[str], cwd: str | None = None) -> str:
    """Run a subprocess command and return its ``stdout``.

    Args:
        cmd: Command and arguments to execute.
        cwd: Directory in which to run the command.

    Returns:
        Captured standard output from the command.

    Raises:
        subprocess.CalledProcessError: If the command exits with a non-zero status.
    """

    res = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        raise subprocess.CalledProcessError(
            res.returncode,
            shlex.join(cmd),
            output=res.stdout,
            stderr=res.stderr,
        )
    return res.stdout


def changed_paths(base: str, head: str, cwd: str | None = None) -> set[str]:
    """Return paths changed between two git references.

    Args:
        base: Base git reference.
        head: Head git reference.
        cwd: Repository path.

    Returns:
        Set of file paths that differ between the two refs.
    """

    out = _run(["git", "diff", "--name-only", f"{base}..{head}"], cwd)
    return {line.strip() for line in out.splitlines() if line.strip()}


@lru_cache(maxsize=None)
def _list_py_files_at_ref_cached(
    ref: str,
    roots: tuple[str, ...],
    ignore_globs: tuple[str, ...],
    cwd: str | None,
) -> frozenset[str]:
    """Return cached Python file paths for a given ref.

    Args:
        ref: Git reference to inspect.
        roots: Root directories to include.
        ignore_globs: Glob patterns to exclude.
        cwd: Repository path.

    Returns:
        Frozen set of matching Python file paths.
    """

    out = _run(["git", "ls-tree", "-r", "--name-only", ref], cwd)
    paths: set[str] = set()
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
            paths.add(s)
    return frozenset(paths)


def list_py_files_at_ref(
    ref: str,
    roots: Iterable[str],
    ignore_globs: Iterable[str] | None = None,
    cwd: str | None = None,
) -> set[str]:
    """List Python files under given roots at a git ref.

    Results are cached per ``(ref, tuple(roots), tuple(ignores))`` for improved
    performance. Use ``list_py_files_at_ref.cache_clear()`` to invalidate.

    Args:
        ref: Git reference to inspect.
        roots: Root directories to include.
        ignore_globs: Optional glob patterns to exclude.
        cwd: Repository path.

    Returns:
        Set of matching Python file paths.
    """

    roots_tuple = tuple(roots)
    ignores_tuple = tuple(ignore_globs or ())
    return set(_list_py_files_at_ref_cached(ref, roots_tuple, ignores_tuple, cwd))


list_py_files_at_ref.cache_clear = _list_py_files_at_ref_cached.cache_clear  # type: ignore[attr-defined]


@lru_cache(maxsize=None)
def _read_file_at_ref_cached(ref: str, path: str, cwd: str | None) -> str | None:
    """Return cached file contents for a ref and path.

    Args:
        ref: Git reference at which to read the file.
        path: File path relative to the repository root.
        cwd: Repository path.

    Returns:
        File contents, or ``None`` if the file does not exist at ``ref``.
    """

    try:
        return _run(["git", "show", f"{ref}:{path}"], cwd)
    except subprocess.CalledProcessError:
        return None


def read_file_at_ref(ref: str, path: str, cwd: str | None = None) -> str | None:
    """Read the contents of ``path`` at ``ref`` if it exists.

    Results are cached per ``(ref, path, cwd)`` for improved performance. Use
    ``read_file_at_ref.cache_clear()`` to invalidate.

    Args:
        ref: Git reference at which to read the file.
        path: File path relative to the repository root.
        cwd: Repository path.

    Returns:
        File contents, or ``None`` if the file does not exist at ``ref``.
    """

    return _read_file_at_ref_cached(ref, path, cwd)


read_file_at_ref.cache_clear = _read_file_at_ref_cached.cache_clear  # type: ignore[attr-defined]


@lru_cache(maxsize=None)
def _read_files_at_ref_cached(
    ref: str, paths: tuple[str, ...], cwd: str | None
) -> dict[str, str | None]:
    """Return cached contents for multiple paths at a git reference.

    Args:
        ref: Git reference at which to read files.
        paths: Iterable of file paths relative to the repository root.
        cwd: Repository path.

    Returns:
        Mapping of file paths to their contents or ``None`` if a file does not
        exist at ``ref``.
    """

    if not paths:
        return {}
    spec = "\n".join(f"{ref}:{p}" for p in paths) + "\n"
    res = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=cwd,
        input=spec.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if res.returncode != 0:
        raise subprocess.CalledProcessError(
            res.returncode,
            "git cat-file --batch",
            output=res.stdout.decode(),
            stderr=res.stderr.decode(),
        )

    out = BytesIO(res.stdout)
    results: dict[str, str | None] = {}
    for path in paths:
        header = out.readline().decode().strip()
        if not header:
            results[path] = None
            continue
        if header.endswith(" missing"):
            results[path] = None
            continue
        _sha, _typ, size_str = header.split()
        size = int(size_str)
        content = out.read(size).decode()
        out.read(1)
        results[path] = content
    return results


def read_files_at_ref(
    ref: str, paths: Iterable[str], cwd: str | None = None
) -> dict[str, str | None]:
    """Read multiple file contents at ``ref`` in a single subprocess call.

    Results are cached per ``(ref, tuple(paths), cwd)`` for improved
    performance. Use ``read_files_at_ref.cache_clear()`` to invalidate.

    Args:
        ref: Git reference at which to read files.
        paths: Iterable of file paths relative to the repository root.
        cwd: Repository path.

    Returns:
        Mapping of file paths to their contents or ``None`` if a file does not
        exist at ``ref``.
    """

    paths_tuple = tuple(paths)
    return dict(_read_files_at_ref_cached(ref, paths_tuple, cwd))


read_files_at_ref.cache_clear = _read_files_at_ref_cached.cache_clear  # type: ignore[attr-defined]


def last_release_commit(cwd: str | None = None) -> str | None:
    """Return the most recent release commit created by bumpwright.

    Args:
        cwd: Repository path to inspect.

    Returns:
        Hash of the latest ``chore(release):`` commit or ``None`` if not found.
    """

    try:
        out = _run(
            ["git", "log", "-n", "1", "--grep", "^chore(release):", "--format=%H"],
            cwd,
        )
    except subprocess.CalledProcessError:
        return None
    return out.strip() or None


def collect_commits(
    base: str, head: str, cwd: str | None = None
) -> list[tuple[str, str]]:
    """Collect commit metadata between two references.

    Args:
        base: Older git reference (exclusive).
        head: Newer git reference (inclusive).
        cwd: Optional repository path.

    Returns:
        List of ``(short_sha, subject)`` tuples ordered newest first.
    """

    out = _run(["git", "log", "--format=%h%x09%s", f"{base}..{head}"], cwd)
    commits: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, subject = line.split("\t", 1)
        commits.append((sha, subject))
    return commits
