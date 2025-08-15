from __future__ import annotations

import shlex
import subprocess
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, List, Optional, Set


def _run(cmd: List[str], cwd: str | None = None) -> str:
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


def changed_paths(base: str, head: str, cwd: str | None = None) -> Set[str]:
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


def list_py_files_at_ref(
    ref: str,
    roots: Iterable[str],
    ignore_globs: Iterable[str] | None = None,
    cwd: str | None = None,
) -> Set[str]:
    """List Python files under given roots at a git ref.

    Args:
        ref: Git reference to inspect.
        roots: Root directories to include.
        ignore_globs: Optional glob patterns to exclude.
        cwd: Repository path.

    Returns:
        Set of matching Python file paths.
    """

    out = _run(["git", "ls-tree", "-r", "--name-only", ref], cwd)
    paths: Set[str] = set()
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
    return paths


def read_file_at_ref(ref: str, path: str, cwd: str | None = None) -> Optional[str]:
    """Read the contents of ``path`` at ``ref`` if it exists.

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
