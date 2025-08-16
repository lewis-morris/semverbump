"""Detect changes in web application routes across git references.

The analyser walks Python modules looking for decorator-based route
definitions used by frameworks such as Flask or FastAPI.  It compares the
collected routes between revisions to flag additions, removals, and parameter
changes.  Only straightforward decorator patterns are recognised, so routes
registered dynamically or via framework-specific helpers may be missed.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from dataclasses import dataclass

from ..compare import Impact
from ..config import Config
from ..gitutils import list_py_files_at_ref
from . import register
from .utils import _is_const_str, parse_python_source

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}


@dataclass(frozen=True)
class Route:
    """Represent a single HTTP route."""

    path: str
    method: str
    params: dict[str, bool]  # True if required


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


def extract_routes_from_source(code: str | ast.AST) -> dict[tuple[str, str], Route]:
    """Extract routes from source code.

    Supports synchronous and asynchronous route handlers.

    Args:
        code: Module source text or a pre-parsed AST.

    Returns:
        Mapping of ``(path, method)`` to :class:`Route` objects.
    """

    tree = ast.parse(code) if isinstance(code, str) else code
    routes: dict[tuple[str, str], Route] = {}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
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
                        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                            methods = [elt.value.upper() for elt in kw.value.elts if _is_const_str(elt)]
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


def _build_routes_at_ref(ref: str, roots: Iterable[str], ignores: Iterable[str]) -> dict[tuple[str, str], Route]:
    """Collect routes for all modules under given roots at a git ref.

    Args:
        ref: Git reference to inspect.
        roots: Root directories to search for Python modules.
        ignores: Glob patterns to exclude from scanning.

    Returns:
        Mapping of ``(path, method)`` to :class:`Route` objects present at ``ref``.
    """

    out: dict[tuple[str, str], Route] = {}
    for path in list_py_files_at_ref(ref, roots, ignore_globs=ignores):
        tree = parse_python_source(ref, path)
        if tree is not None:
            out.update(extract_routes_from_source(tree))
    return out


def diff_routes(old: dict[tuple[str, str], Route], new: dict[tuple[str, str], Route]) -> list[Impact]:
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
class WebRoutesAnalyser:
    """Analyser plugin for web application routes."""

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyser with configuration."""
        self.cfg = cfg

    def collect(self, ref: str) -> dict[tuple[str, str], Route]:
        """Collect route definitions at ``ref``.

        Args:
            ref: Git reference to inspect.

        Returns:
            Mapping of ``(path, method)`` to :class:`Route` objects.
        """

        return _build_routes_at_ref(ref, self.cfg.project.public_roots, self.cfg.ignore.paths)

    def compare(self, old: dict[tuple[str, str], Route], new: dict[tuple[str, str], Route]) -> list[Impact]:
        """Compare two route mappings and return impacts.

        Args:
            old: Baseline route mapping.
            new: Updated route mapping.

        Returns:
            List of impacts describing route changes.
        """

        return diff_routes(old, new)
