"""Extract and represent a package's public API using the stdlib AST.

This module inspects Python source code to determine the exposed public API.
It uses :mod:`ast` to avoid heavyweight third‑party dependencies while still
capturing function and method signatures accurately.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

# --------- Data model ---------


@dataclass(frozen=True)
class Param:
    """Function parameter description.

    Attributes:
        name: Parameter name.
        kind: Parameter kind (``"posonly"``, ``"pos"``, ``"vararg"``,
            ``"kwonly"``, or ``"varkw"``).
        default: Default value expression if present.
        annotation: Type annotation if present.
    """

    name: str
    kind: str  # "posonly" | "pos" | "vararg" | "kwonly" | "varkw"
    default: str | None
    annotation: str | None


@dataclass(frozen=True)
class FuncSig:
    """Public function or method signature.

    Attributes:
        fullname: Fully qualified name (``module:func`` or
            ``module:Class.method``).
        params: Ordered parameter definitions.
        returns: Return annotation if specified.
    """

    fullname: str  # e.g. pkg.mod:func  or pkg.mod:Class.method
    params: tuple[Param, ...]
    returns: str | None


PublicAPI = dict[str, FuncSig]  # symbol -> function signature (functions & methods)


# --------- Helpers ---------


def _render_expr(node: ast.AST | None) -> str | None:
    """Render arbitrary expressions such as default values.

    Args:
        node: AST node to render.

    Returns:
        String representation of ``node`` or ``None`` if ``node`` is ``None``.
    """

    return ast.unparse(node) if node is not None else None


def _render_type(ann: ast.AST | None) -> str | None:
    """Safely render type annotations for parameters and returns.

    Args:
        ann: Annotation node to render.

    Returns:
        String form of the annotation or ``None`` if absent.
    """

    return ast.unparse(ann) if ann is not None else None


def _parse_exports(mod: ast.Module) -> set[str] | None:
    """Parse ``__all__`` definitions from a module if present.

    Args:
        mod: Parsed module.

    Returns:
        Set of exported symbol names or ``None`` if ``__all__`` is undefined.
    """

    for stmt in mod.body:
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1:
                continue
            tgt = stmt.targets[0]
            if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                if isinstance(stmt.value, (ast.List, ast.Tuple)):
                    vals: list[str] = []
                    for el in stmt.value.elts:
                        if isinstance(el, ast.Constant) and isinstance(el.value, str):
                            vals.append(el.value)
                    return set(vals)
    return None


def _param_list(args: ast.arguments) -> list[Param]:
    """Convert AST parameters to :class:`Param` instances.

    Args:
        args: Function arguments node from the AST.

    Returns:
        Ordered list of parameter descriptors.
    """

    out: list[Param] = []

    def _ann(node: ast.expr | None) -> str | None:
        return _render_type(node) if node is not None else None

    # Positional-only and positional params share defaults
    posonly = list(args.posonlyargs)
    pos = list(args.args)
    defaults = list(args.defaults)
    total = len(posonly) + len(pos)
    d_start = total - len(defaults)
    idx = 0

    for p in posonly + pos:
        default = _render_expr(defaults[idx - d_start]) if idx >= d_start else None
        kind = "posonly" if idx < len(posonly) else "pos"
        out.append(Param(p.arg, kind, default, _ann(p.annotation)))
        idx += 1

    # Var positional
    if args.vararg:
        out.append(Param(args.vararg.arg, "vararg", None, _ann(args.vararg.annotation)))

    # Keyword-only params
    for param, default in zip(args.kwonlyargs, args.kw_defaults):
        out.append(
            Param(param.arg, "kwonly", _render_expr(default), _ann(param.annotation))
        )

    # Var keyword
    if args.kwarg:
        out.append(Param(args.kwarg.arg, "varkw", None, _ann(args.kwarg.annotation)))

    return out


def _is_public(name: str) -> bool:
    """Return whether ``name`` represents a public symbol.

    Args:
        name: Symbol name to evaluate.

    Returns:
        ``True`` if ``name`` does not begin with an underscore.
    """

    return not name.startswith("_")


# --------- Visitor that collects public API ---------


class _APIVisitor(ast.NodeVisitor):
    """Collect public function and method signatures from a module."""

    def __init__(self, module_name: str, exports: set[str] | None) -> None:
        """Initialize the visitor.

        Args:
            module_name: Name of the module being inspected.
            exports: Explicitly exported symbols if ``__all__`` is defined.
                ``None`` indicates that all public symbols are considered.
        """

        self.module_name = module_name
        self.exports = exports
        self.sigs: list[FuncSig] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: D401
        """Collect function definitions."""

        fn = node.name
        if self.exports is not None and fn not in self.exports:
            return
        if not _is_public(fn):
            return
        params = tuple(_param_list(node.args))
        ret = _render_type(node.returns)
        self.sigs.append(FuncSig(f"{self.module_name}:{fn}", params, ret))

    # Async functions have the same signature representation
    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: D401
        """Collect method signatures from public classes."""

        cname = node.name
        if self.exports is not None and cname not in self.exports:
            return
        if not _is_public(cname):
            return

        for elt in node.body:
            if isinstance(elt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                mname = elt.name
                if not _is_public(mname):
                    continue
                params = tuple(_param_list(elt.args))
                ret = _render_type(elt.returns)
                self.sigs.append(
                    FuncSig(f"{self.module_name}:{cname}.{mname}", params, ret)
                )


def module_name_from_path(root: str, path: str) -> str:
    """Convert a file path to a module name relative to ``root``.

    Args:
        root: Root directory of the package.
        path: File path under ``root``.

    Returns:
        Dotted module path corresponding to ``path``.

    Raises:
        ValueError: If ``path`` is not located within ``root``.
    """

    try:
        rel = Path(path).with_suffix("").relative_to(Path(root))
    except ValueError as exc:
        raise ValueError(f"{path!r} is not relative to {root!r}") from exc
    return ".".join(rel.parts)


def extract_public_api_from_source(module_name: str, code: str) -> PublicAPI:
    """Extract the public API from Python source code.

    Args:
        module_name: Name of the module represented by ``code``.
        code: Source code to analyze.

    Returns:
        Mapping of symbol names to :class:`FuncSig` objects.
    """

    mod = ast.parse(code)
    exports = _parse_exports(mod)
    visitor = _APIVisitor(module_name, exports)
    visitor.visit(mod)
    return {s.fullname: s for s in visitor.sigs}


__all__ = [
    "Param",
    "FuncSig",
    "PublicAPI",
    "module_name_from_path",
    "extract_public_api_from_source",
]
