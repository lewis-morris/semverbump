"""Analyzer for Alembic database migrations.

The utilities here parse migration scripts and flag schema changes such as
added or removed columns. The analyzer reports these findings as public API
impacts so they can influence semantic version recommendations.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Optional

from ..compare import Impact
from ..config import Migrations
from ..gitutils import changed_paths, read_file_at_ref


class _UpgradeVisitor(ast.NodeVisitor):
    """AST visitor that records schema-changing operations."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.impacts: List[Impact] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: D401
        """Record relevant Alembic operations."""

        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Name
        ):
            if node.func.value.id == "op":
                attr = node.func.attr
                if attr == "drop_column":
                    self.impacts.append(Impact("major", self.path, "Dropped column"))
                elif attr == "add_column":
                    impact = _analyze_add_column(node, self.path)
                    if impact:
                        self.impacts.append(impact)
                elif attr == "create_index":
                    self.impacts.append(Impact("minor", self.path, "Added index"))
        self.generic_visit(node)


def _analyze_add_column(node: ast.Call, path: str) -> Optional[Impact]:
    """Determine the impact of an ``op.add_column`` call."""

    column = None
    for arg in node.args:
        if (
            isinstance(arg, ast.Call)
            and isinstance(arg.func, ast.Attribute)
            and arg.func.attr == "Column"
        ):
            column = arg
            break
    if column is None:
        return None

    kwargs = {kw.arg: kw.value for kw in column.keywords if kw.arg}
    nullable = True
    if "nullable" in kwargs and isinstance(kwargs["nullable"], ast.Constant):
        nullable = bool(kwargs["nullable"].value)
    has_default = "default" in kwargs or "server_default" in kwargs
    if not nullable and not has_default:
        return Impact("major", path, "Added non-nullable column")
    return Impact("minor", path, "Added column")


def _analyze_content(path: str, content: str) -> List[Impact]:
    """Parse migration source and collect impacts."""

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    impacts: List[Impact] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            visitor = _UpgradeVisitor(path)
            for stmt in node.body:
                visitor.visit(stmt)
            impacts.extend(visitor.impacts)
    return impacts


def analyze_migrations(
    base: str, head: str, config: Migrations, cwd: str | Path | None = None
) -> List[Impact]:
    """Analyze Alembic migrations between two git references.

    Args:
        base: Base git reference to compare from.
        head: Head git reference to compare to.
        config: Migration analyzer settings.
        cwd: Repository root.

    Returns:
        List of detected schema change impacts.
    """

    dirs = [str(Path(p)) for p in config.paths]
    impacts: List[Impact] = []
    for path in changed_paths(base, head, cwd=cwd):
        if not path.endswith(".py"):
            continue
        if not any(path == d or path.startswith(f"{d}/") for d in dirs):
            continue
        content = read_file_at_ref(head, path, cwd=cwd)
        if content is None:
            continue
        impacts.extend(_analyze_content(path, content))
    return impacts
