"""Shared helpers for analyser modules."""

from __future__ import annotations

import ast
from collections.abc import Iterable, Iterator

from ..gitutils import list_py_files_at_ref, read_files_at_ref


def _is_const_str(node: ast.AST) -> bool:
    """Return whether ``node`` is an ``ast.Constant`` string.

    Args:
        node: AST node to inspect.

    Returns:
        ``True`` if ``node`` represents a constant string literal.
    """

    return isinstance(node, ast.Constant) and isinstance(node.value, str)


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

    paths = list(list_py_files_at_ref(ref, roots, ignore_globs=ignore_globs, cwd=cwd))
    contents = read_files_at_ref(ref, paths, cwd=cwd)
    for path in paths:
        code = contents.get(path)
        if code is not None:
            yield path, code
