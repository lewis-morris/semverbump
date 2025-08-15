from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import libcst as cst

# --------- Data model ---------

@dataclass(frozen=True)
class Param:
    name: str
    kind: str           # "posonly" | "pos" | "vararg" | "kwonly" | "varkw"
    default: Optional[str]
    annotation: Optional[str]

@dataclass(frozen=True)
class FuncSig:
    fullname: str       # e.g. pkg.mod:func  or pkg.mod:Class.method
    params: Tuple[Param, ...]
    returns: Optional[str]

PublicAPI = Dict[str, FuncSig]   # symbol -> function signature (functions & methods)

# --------- Helpers ---------

def _render(node: Optional[cst.CSTNode]) -> Optional[str]:
    return cst.Module([]).code_for_node(node) if node is not None else None

def _parse_exports(mod: cst.Module) -> Optional[set[str]]:
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
    out: List[Param] = []
    def _def(p: cst.Param) -> Optional[str]:
        return _render(p.default) if p.default else None
    def _ann(p: cst.Param) -> Optional[str]:
        return _render(p.annotation) if p.annotation else None

    for p in params.posonly_params:
        out.append(Param(p.name.value, "posonly", _def(p), _ann(p)))
    for p in params.params:
        out.append(Param(p.name.value, "pos", _def(p), _ann(p)))
    if params.star_arg:
        p = params.star_arg
        out.append(Param(p.name.value, "vararg", None, _ann(p)))
    for p in params.kwonly_params:
        out.append(Param(p.name.value, "kwonly", _def(p), _ann(p)))
    if params.star_kwarg:
        p = params.star_kwarg
        out.append(Param(p.name.value, "varkw", None, _ann(p)))
    return out

def _is_public(name: str) -> bool:
    return not name.startswith("_")

# --------- Visitor that collects public API ---------

class _APIVisitor(cst.CSTVisitor):
    def __init__(self, module_name: str, exports: Optional[set[str]]):
        self.module_name = module_name
        self.exports = exports
        self.sigs: List[FuncSig] = []

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        fn = node.name.value
        if self.exports is not None and fn not in self.exports:
            return
        if not _is_public(fn):
            return
        params = tuple(_param_list(node.params))
        ret = _render(node.returns)
        self.sigs.append(FuncSig(f"{self.module_name}:{fn}", params, ret))

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        cname = node.name.value
        if self.exports is not None and cname not in self.exports:
            # If __all__ explicitly exports the class name list, we honor it
            if not any(isinstance(b, cst.SimpleStatementLine) for b in node.body.body):
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
                ret = _render(elt.returns)
                self.sigs.append(FuncSig(f"{self.module_name}:{cname}.{mname}", params, ret))

def module_name_from_path(root: str, path: str) -> str:
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
    mod = cst.parse_module(code)
    exports = _parse_exports(mod)
    v = _APIVisitor(module_name, exports)
    mod.visit(v)
    return {s.fullname: s for s in v.sigs}
