"""Web route analyzer for Flask and FastAPI apps."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from ..compare import Impact
from ..config import Config
from ..gitutils import list_py_files_at_ref, read_file_at_ref
from . import register

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}


@dataclass(frozen=True)
class Route:
    """Represent a single HTTP route."""

    path: str
    method: str
    params: Dict[str, bool]  # True if required


def _is_const_str(node: ast.AST) -> bool:
    """Return ``True`` if ``node`` is a constant string."""
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _extract_params(args: ast.arguments) -> Dict[str, bool]:
    """Extract function parameters and whether they are required.

    Args:
        args: AST arguments object.

    Returns:
        Mapping of parameter name to required flag.
    """

    params: Dict[str, bool] = {}
    pos = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(pos) - len(args.defaults)) + list(args.defaults)
    for a, d in zip(pos, defaults):
        if a.arg == "self":
            continue
        required = d is None
        params[a.arg] = required
    for a, d in zip(args.kwonlyargs, args.kw_defaults):
        required = d is None
        params[a.arg] = required
    return params


def extract_routes_from_source(code: str) -> Dict[Tuple[str, str], Route]:
    """Extract routes from source code.

    Args:
        code: Module source code.

    Returns:
        Mapping of (path, method) to :class:`Route` objects.
    """

    tree = ast.parse(code)
    routes: Dict[Tuple[str, str], Route] = {}

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
) -> Dict[Tuple[str, str], Route]:
    """Collect routes for all modules under given roots at a git ref."""

    out: Dict[Tuple[str, str], Route] = {}
    for root in roots:
        for path in list_py_files_at_ref(ref, [root], ignore_globs=ignores):
            code = read_file_at_ref(ref, path)
            if code is None:
                continue
            out.update(extract_routes_from_source(code))
    return out


def diff_routes(
    old: Dict[Tuple[str, str], Route], new: Dict[Tuple[str, str], Route]
) -> List[Impact]:
    """Compute impacts between two route mappings."""

    impacts: List[Impact] = []

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


@register("web_routes")
class WebRoutesAnalyzer:
    """Analyzer plugin for web application routes."""

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyzer with configuration."""
        self.cfg = cfg

    def collect(self, ref: str) -> Dict[Tuple[str, str], Route]:
        """Collect route definitions at ``ref``."""
        return _build_routes_at_ref(
            ref, self.cfg.project.public_roots, self.cfg.ignore.paths
        )

    def compare(
        self, old: Dict[Tuple[str, str], Route], new: Dict[Tuple[str, str], Route]
    ) -> List[Impact]:
        """Compare two route mappings and return impacts."""
        return diff_routes(old, new)
