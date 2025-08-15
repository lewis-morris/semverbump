"""Extract and represent a package's public API using LibCST."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:  # pragma: no cover - needed for linting when dependency missing
    import libcst as cst
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError("libcst is required to analyze public APIs") from exc

# --------- Data model ---------


@dataclass(frozen=True)
class Param:
    """Function parameter description.

    Attributes:
        name: Parameter name.
        kind: Parameter kind (``"posonly"``, ``"pos"``, ``"vararg"``, ``"kwonly"``, or ``"varkw"``).
        default: Default value expression if present.
        annotation: Type annotation if present.
    """

    name: str
    kind: str  # "posonly" | "pos" | "vararg" | "kwonly" | "varkw"
    default: Optional[str]
    annotation: Optional[str]


@dataclass(frozen=True)
class FuncSig:
    """Public function or method signature.

    Attributes:
        fullname: Fully qualified name (``module:func`` or ``module:Class.method``).
        params: Ordered parameter definitions.
        returns: Return annotation if specified.
    """

    fullname: str  # e.g. pkg.mod:func  or pkg.mod:Class.method
    params: Tuple[Param, ...]
    returns: Optional[str]


PublicAPI = Dict[str, FuncSig]  # symbol -> function signature (functions & methods)

# --------- Helpers ---------


def _render_expr(node: cst.CSTNode | None) -> str | None:
    """Render arbitrary expressions (defaults, etc.)."""
    return cst.Module([]).code_for_node(node) if node is not None else None


def _render_type(ann: cst.Annotation | None) -> str | None:
    """Safely render type annotations (params & returns)."""
    if ann is None:
        return None
    # LibCST’s Annotation needs its inner expression rendered, not the wrapper.
    return cst.Module([]).code_for_node(ann.annotation)


def _parse_exports(mod: cst.Module) -> Optional[set[str]]:
    """Parse ``__all__`` definitions from a module if present.

    Args:
        mod: Parsed module.

    Returns:
        Set of exported symbol names or ``None`` if ``__all__`` is undefined.
    """

    # Honor simple __all__ = ["name", "name2"] at module top level
    for s in mod.body:
        if not isinstance(s, cst.SimpleStatementLine):
            continue
        for a in s.body:
            if not isinstance(a, cst.Assign):
                continue
            tgt = a.targets[0].target
            if isinstance(tgt, cst.Name) and tgt.value == "__all__":
                if isinstance(a.value, (cst.List, cst.Tuple)):
                    vals: list[str] = []
                    for el in a.value.elements:
                        v = el.value
                        if isinstance(v, cst.SimpleString):
                            # safe: evaluated_value is just a literal
                            vals.append(v.evaluated_value)
                    return set(vals)
    return None


def _param_list(params: cst.Parameters) -> List[Param]:
    """Convert LibCST parameters to :class:`Param` instances.

    Args:
        params: LibCST parameter container.

    Returns:
        Ordered list of :class:`Param` definitions.
    """

    out: List[Param] = []

    def _def(p: cst.Param) -> Optional[str]:
        return _render_expr(p.default) if p.default else None

    def _ann(p: cst.Param) -> Optional[str]:
        return _render_type(p.annotation) if p.annotation else None

    for p in params.posonly_params:
        out.append(Param(p.name.value, "posonly", _def(p), _ann(p)))
    for p in params.params:
        out.append(Param(p.name.value, "pos", _def(p), _ann(p)))
    # *args or bare * (keyword-only marker)
    sa = params.star_arg
    if isinstance(sa, cst.Param):
        # real vararg like *args
        out.append(Param(sa.name.value, "vararg", None, _ann(sa)))
    else:
        # bare "*" (no vararg) — just a marker; nothing to add
        pass
    for p in params.kwonly_params:
        out.append(Param(p.name.value, "kwonly", _def(p), _ann(p)))
    if params.star_kwarg:
        p = params.star_kwarg
        out.append(Param(p.name.value, "varkw", None, _ann(p)))
    return out


def _is_public(name: str) -> bool:
    """Return ``True`` if ``name`` represents a public symbol."""
    return not name.startswith("_")


# --------- Visitor that collects public API ---------


class _APIVisitor(cst.CSTVisitor):
    """Collect public function and method signatures from a module."""

    def __init__(self, module_name: str, exports: Optional[set[str]]):
        """Initialize the visitor.

        Args:
            module_name: Name of the module being inspected.
            exports: Explicitly exported symbols if ``__all__`` is defined.
        """

        self.module_name = module_name
        self.exports = exports
        self.sigs: List[FuncSig] = []

    def visit_FunctionDef(
        self, node: cst.FunctionDef
    ) -> None:  # noqa: D401  # pylint: disable=invalid-name
        """Collect function definitions."""

        fn = node.name.value
        if self.exports is not None and fn not in self.exports:
            return
        if not _is_public(fn):
            return
        params = tuple(_param_list(node.params))
        ret = _render_type(node.returns)
        self.sigs.append(FuncSig(f"{self.module_name}:{fn}", params, ret))

    def visit_ClassDef(
        self, node: cst.ClassDef
    ) -> None:  # noqa: D401  # pylint: disable=invalid-name
        """Collect method signatures from public classes."""

        cname = node.name.value
        if self.exports is not None and cname not in self.exports:
            return
        if not _is_public(cname):
            return

        # Methods
        for elt in node.body.body:
            if isinstance(elt, cst.FunctionDef):
                mname = elt.name.value
                if not _is_public(mname):
                    continue
                params = tuple(_param_list(elt.params))
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
    """

    # Convert path under root into a module name (strip .py and replace / with .)
    rp = Path(path).with_suffix("")
    parts = list(rp.parts)
    # remove common leading '.' or root
    root_parts = list(Path(root).parts)
    while root_parts and parts and parts[0] == root_parts[0]:
        parts.pop(0)
        root_parts.pop(0)
    return ".".join(parts)


def extract_public_api_from_source(module_name: str, code: str) -> PublicAPI:
    """Extract the public API from Python source code.

    Args:
        module_name: Name of the module represented by ``code``.
        code: Source code to analyze.

    Returns:
        Mapping of symbol names to :class:`FuncSig` objects.
    """

    mod = cst.parse_module(code)
    exports = _parse_exports(mod)
    v = _APIVisitor(module_name, exports)
    mod.visit(v)
    return {s.fullname: s for s in v.sigs}
