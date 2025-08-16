"""Analyser for Alembic database migrations.

The utilities here parse migration scripts and flag schema changes such as
added or removed columns. The analyser reports these findings as public API
impacts so they can influence semantic version recommendations.
"""

from __future__ import annotations

import ast
from pathlib import Path

from ..compare import Impact
from ..config import Config, Migrations
from ..gitutils import changed_paths, read_files_at_ref
from . import register


class _UpgradeVisitor(ast.NodeVisitor):
    """AST visitor that records schema-changing operations."""

    def __init__(self, path: str) -> None:
        """Create a visitor for a specific migration file.

        Args:
            path: Path to the migration being inspected.
        """

        self.path = path
        self.impacts: list[Impact] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: D401
        """Record relevant Alembic operations."""

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
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
                elif attr == "drop_table":
                    self.impacts.append(Impact("major", self.path, "Dropped table"))
                elif attr == "rename_column":
                    self.impacts.append(Impact("major", self.path, "Renamed column"))
                elif attr == "alter_column":
                    impact = _analyze_alter_column(node, self.path)
                    if impact:
                        self.impacts.append(impact)
                elif attr == "drop_index":
                    self.impacts.append(Impact("minor", self.path, "Dropped index"))
        self.generic_visit(node)


def _analyze_add_column(node: ast.Call, path: str) -> Impact | None:
    """Determine the impact of an ``op.add_column`` call.

    Args:
        node: AST call node representing ``op.add_column``.
        path: Path of the migration file being analyzed.

    Returns:
        Impact describing the column addition, or ``None`` if the operation
        cannot be assessed.
    """

    column = None
    for arg in node.args:
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == "Column":
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


def _analyze_alter_column(node: ast.Call, path: str) -> Impact | None:
    """Determine the impact of an ``op.alter_column`` call.

    Args:
        node: AST call node representing ``op.alter_column``.
        path: Path of the migration file being analyzed.

    Returns:
        Impact describing the alteration, or ``None`` if the operation cannot
        be assessed.
    """

    kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
    if "nullable" in kwargs and isinstance(kwargs["nullable"], ast.Constant):
        nullable = bool(kwargs["nullable"].value)
        if not nullable:
            return Impact("major", path, "Altered column to be non-nullable")
        return Impact("minor", path, "Altered column")
    return Impact("major", path, "Altered column")


def _analyze_content(path: str, content: str) -> list[Impact]:
    """Parse migration source and collect impacts.

    Args:
        path: Path of the migration file.
        content: Source code of the migration.

    Returns:
        List of detected impacts within the migration.
    """

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    impacts: list[Impact] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            visitor = _UpgradeVisitor(path)
            for stmt in node.body:
                visitor.visit(stmt)
            impacts.extend(visitor.impacts)
    return impacts


def analyze_migrations(base: str, head: str, config: Migrations, cwd: str | Path | None = None) -> list[Impact]:
    """Analyze Alembic migrations between two git references.

    Args:
        base: Base git reference to compare from.
        head: Head git reference to compare to.
        config: Migration analyser settings.
        cwd: Repository root.

    Returns:
        List of detected schema change impacts.
    """

    dirs = [str(Path(p)) for p in config.paths]
    relevant: list[str] = []
    for path in changed_paths(base, head, cwd=cwd):
        if not path.endswith(".py"):
            continue
        if any(path == d or path.startswith(f"{d}/") for d in dirs):
            relevant.append(path)
    contents = read_files_at_ref(head, relevant, cwd=cwd)
    impacts: list[Impact] = []
    for path, content in contents.items():
        if content is None:
            continue
        impacts.extend(_analyze_content(path, content))
    return impacts


@register("migrations", "Analyze database migrations for schema changes.")
class MigrationsAnalyser:
    """Analyser plugin for Alembic migrations."""

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyser with configuration.

        Args:
            cfg: Global configuration object.
        """

        self.cfg = cfg

    def collect(self, ref: str) -> str:
        """Collect analyser state for ``ref``.

        Args:
            ref: Git reference to inspect.

        Returns:
            The provided git reference for later comparison.
        """

        return ref

    def compare(self, old: str, new: str) -> list[Impact]:
        """Compare two git references and return migration impacts.

        Args:
            old: Baseline git reference.
            new: Updated git reference.

        Returns:
            List of detected schema change impacts.
        """

        return analyze_migrations(old, new, self.cfg.migrations)
