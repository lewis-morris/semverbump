"""Detect HTTP route changes across git references.

This module parses Flask and FastAPI route decorators to track endpoint
modifications. Each detected route is returned as a :class:`Route` dataclass
containing the URL ``path``, HTTP ``method``, and a ``params`` mapping of
parameter names to a boolean flag indicating whether the parameter is required.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from dataclasses import dataclass

from ..compare import Impact
from ..config import Config
from . import register
from .utils import iter_py_files_at_ref

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}


@dataclass(frozen=True)
class Route:
    """Represent a single HTTP route."""

    path: str
    method: str
    params: dict[str, bool]  # True if required


def _is_const_str(node: ast.AST) -> bool:
    """Return whether ``node`` is a constant string.

    Args:
        node: AST node to inspect.

    Returns:
        ``True`` if ``node`` represents a string literal.
    """

    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _extract_params(args: ast.arguments) -> dict[str, bool]:
    """Extract function parameters and whether they are required.

    Args:
        args: AST arguments object.

    Returns:
        Mapping of parameter name to required flag.
    """

    pos = list(args.posonlyargs) + list(args.args)
    pos_defaults = [None] * (len(pos) - len(args.defaults)) + list(args.defaults)
    params = {a.arg: d is None for a, d in zip(pos, pos_defaults) if a.arg != "self"}
    params.update({a.arg: d is None for a, d in zip(args.kwonlyargs, args.kw_defaults)})
    return params


def extract_routes_from_source(code: str) -> dict[tuple[str, str], Route]:
    """Extract routes from source code.

    Args:
        code: Module source code.

    Returns:
        Mapping of (path, method) to :class:`Route` objects.
    """

    tree = ast.parse(code)
    routes: dict[tuple[str, str], Route] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        path = None
        methods: Iterable[str] | None = None
        for deco in node.decorator_list:
            if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                name = deco.func.attr.lower()
                if name == "route":  # Flask
                    if deco.args and _is_const_str(deco.args[0]):
                        path = deco.args[0].value  # type: ignore[assignment]
                    for kw in deco.keywords:
                        if kw.arg == "methods" and isinstance(
                            kw.value, (ast.List, ast.Tuple)
                        ):
                            methods = [
                                elt.value.upper()
                                for elt in kw.value.elts
                                if _is_const_str(elt)
                            ]
                    if methods is None:
                        methods = ["GET"]
                elif name.upper() in HTTP_METHODS:  # FastAPI style
                    if deco.args and _is_const_str(deco.args[0]):
                        path = deco.args[0].value  # type: ignore[assignment]
                        methods = [name.upper()]
        if path and methods:
            params = _extract_params(node.args)
            for m in methods:
                routes[(path, m)] = Route(path, m, params)
    return routes


def _build_routes_at_ref(
    ref: str, roots: Iterable[str], ignores: Iterable[str]
) -> dict[tuple[str, str], Route]:
    """Collect routes for all modules under given roots at a git ref.

    Args:
        ref: Git reference to inspect.
        roots: Root directories to search for Python modules.
        ignores: Glob patterns to exclude from scanning.

    Returns:
        Mapping of ``(path, method)`` to :class:`Route` objects present at ``ref``.
    """

    out: dict[tuple[str, str], Route] = {}
    for _path, code in iter_py_files_at_ref(ref, roots, ignores):
        out.update(extract_routes_from_source(code))
    return out


def diff_routes(
    old: dict[tuple[str, str], Route], new: dict[tuple[str, str], Route]
) -> list[Impact]:
    """Compute impacts between two route mappings.

    Args:
        old: Mapping of routes for the base reference.
        new: Mapping of routes for the head reference.

    Returns:
        List of detected route impacts.
    """

    impacts: list[Impact] = []

    for key in old.keys() - new.keys():
        path, method = key
        impacts.append(Impact("major", f"{method} {path}", "Removed route"))

    for key in new.keys() - old.keys():
        path, method = key
        impacts.append(Impact("minor", f"{method} {path}", "Added route"))

    for key in old.keys() & new.keys():
        op = old[key].params
        np = new[key].params
        path, method = key
        symbol = f"{method} {path}"
        for p in op.keys() - np.keys():
            if op[p]:
                impacts.append(Impact("major", symbol, f"Removed required param '{p}'"))
            else:
                impacts.append(Impact("minor", symbol, f"Removed optional param '{p}'"))
        for p in np.keys() - op.keys():
            if np[p]:
                impacts.append(Impact("major", symbol, f"Added required param '{p}'"))
            else:
                impacts.append(Impact("minor", symbol, f"Added optional param '{p}'"))
        for p in op.keys() & np.keys():
            if op[p] and not np[p]:
                impacts.append(Impact("minor", symbol, f"Param '{p}' became optional"))
            if not op[p] and np[p]:
                impacts.append(Impact("major", symbol, f"Param '{p}' became required"))
    return impacts


@register("web_routes", "Track changes in web application routes.")
class WebRoutesAnalyzer:
    """Analyzer plugin for web application routes."""

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyzer with configuration."""
        self.cfg = cfg

    def collect(self, ref: str) -> dict[tuple[str, str], Route]:
        """Collect route definitions at ``ref``.

        Args:
            ref: Git reference to inspect.

        Returns:
            Mapping of ``(path, method)`` to :class:`Route` objects.
        """

        return _build_routes_at_ref(
            ref, self.cfg.project.public_roots, self.cfg.ignore.paths
        )

    def compare(
        self, old: dict[tuple[str, str], Route], new: dict[tuple[str, str], Route]
    ) -> list[Impact]:
        """Compare two route mappings and return impacts.

        Args:
            old: Baseline route mapping.
            new: Updated route mapping.

        Returns:
            List of impacts describing route changes.
        """

        return diff_routes(old, new)
