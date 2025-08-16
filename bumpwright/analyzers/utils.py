"""Shared helpers for analyzer modules."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from ..gitutils import list_py_files_at_ref, read_file_at_ref


def iter_py_files_at_ref(
    ref: str,
    roots: Iterable[str],
    ignore_globs: Iterable[str] | None = None,
    cwd: str | None = None,
) -> Iterator[tuple[str, str]]:
    """Yield Python file paths and contents for a git reference.

    Args:
        ref: Git reference to inspect.
        roots: Root directories to search for Python modules.
        ignore_globs: Optional glob patterns to exclude.
        cwd: Repository path in which to run git commands.

    Yields:
        Tuples of ``(path, source)`` for each discovered Python file.
    """

    for path in list_py_files_at_ref(ref, roots, ignore_globs=ignore_globs, cwd=cwd):
        code = read_file_at_ref(ref, path, cwd=cwd)
        if code is not None:
            yield path, code
