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


def render_node(node: ast.AST | None) -> str | None:
    """Render AST nodes such as expressions or annotations.

    Args:
        node: AST node to render.

    Returns:
        String representation of the node or ``None`` if ``node`` is ``None``.
    """

    return ast.unparse(node) if node is not None else None


def _parse_exports(mod: ast.Module) -> set[str] | None:
    """Parse ``__all__`` definitions from a module if present.

    The parser understands simple list/tuple literals, ``+`` concatenation,
    and variable references whose values are string literals. This limited
    evaluation avoids executing user code while still supporting common ways of
    constructing ``__all__``.

    Args:
        mod: Parsed module.

    Returns:
        Set of exported symbol names or ``None`` if ``__all__`` is undefined.
    """

    def _eval(node: ast.AST, env: dict[str, list[str]]) -> list[str] | None:
        """Evaluate simple expressions to a list of strings.

        This supports:

        * List or tuple literals containing only string constants.
        * ``+`` concatenation of supported expressions.
        * References to previously assigned names stored in ``env``.
        """

        if isinstance(node, (ast.List, ast.Tuple)):
            out: list[str] = []
            for el in node.elts:
                if isinstance(el, ast.Constant) and isinstance(el.value, str):
                    out.append(el.value)
                else:
                    return None
            return out
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = _eval(node.left, env)
            right = _eval(node.right, env)
            if left is not None and right is not None:
                return left + right
            return None
        if isinstance(node, ast.Name):
            return env.get(node.id)
        return None

    env: dict[str, list[str]] = {}
    for stmt in mod.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            tgt = stmt.targets[0]
            if not isinstance(tgt, ast.Name):
                continue
            evaluated = _eval(stmt.value, env)
            if tgt.id == "__all__":
                return set(evaluated) if evaluated is not None else None
            if evaluated is not None:
                env[tgt.id] = evaluated
    return None


def _positional_params(args: ast.arguments) -> list[Param]:
    """Build positional-only and positional-or-keyword parameters.

    Args:
        args: Function arguments node from the AST.

    Returns:
        Positional parameter descriptors in declaration order.
    """

    posonly = list(args.posonlyargs)
    pos = list(args.args)
    defaults = list(args.defaults)
    # Defaults apply to the tail of the combined positional parameters.
    total = len(posonly) + len(pos)
    d_start = total - len(defaults)
    out: list[Param] = []

    for idx, param in enumerate(posonly + pos):
        default = render_node(defaults[idx - d_start]) if idx >= d_start else None
        kind = "posonly" if idx < len(posonly) else "pos"
        out.append(Param(param.arg, kind, default, render_node(param.annotation)))
    return out


def _vararg_param(args: ast.arguments) -> list[Param]:
    """Return variable positional parameter if present."""

    if args.vararg:
        return [
            Param(args.vararg.arg, "vararg", None, render_node(args.vararg.annotation))
        ]
    return []


def _kwonly_params(args: ast.arguments) -> list[Param]:
    """Build keyword-only parameters in declaration order."""

    out: list[Param] = []
    for param, default in zip(args.kwonlyargs, args.kw_defaults):
        out.append(
            Param(
                param.arg,
                "kwonly",
                render_node(default),
                render_node(param.annotation),
            )
        )
    return out


def _varkw_param(args: ast.arguments) -> list[Param]:
    """Return variable keyword parameter if present."""

    if args.kwarg:
        return [
            Param(args.kwarg.arg, "varkw", None, render_node(args.kwarg.annotation))
        ]
    return []


def _param_list(args: ast.arguments) -> list[Param]:
    """Convert AST parameters to :class:`Param` instances.

    Args:
        args: Function arguments node from the AST.

    Returns:
        Ordered list of parameter descriptors.
    """

    params: list[Param] = []

    # Capture positional-only and positional-or-keyword parameters.
    params.extend(_positional_params(args))

    # Include *args if provided.
    params.extend(_vararg_param(args))

    # Append keyword-only parameters following * or *args.
    params.extend(_kwonly_params(args))

    # Include **kwargs if provided.
    params.extend(_varkw_param(args))

    return params


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
        ret = render_node(node.returns)
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
                ret = render_node(elt.returns)
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
