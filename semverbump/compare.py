from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from .public_api import FuncSig, PublicAPI, Param

@dataclass(frozen=True)
class Impact:
    severity: str   # "major" | "minor" | "patch"
    symbol: str
    reason: str

def _index_params(sig: FuncSig) -> Dict[str, Param]:
    return {p.name: p for p in sig.params}

def compare_funcs(old: FuncSig, new: FuncSig, return_type_change: str = "minor") -> List[Impact]:
    impacts: List[Impact] = []

    oldp = _index_params(old)
    newp = _index_params(new)

    # Removed required param -> major
    for name, op in oldp.items():
        if name not in newp and op.kind in ("posonly", "pos", "kwonly") and op.default is None:
            impacts.append(Impact("major", old.fullname, f"Removed required param '{name}'"))

    # Param kind changed (positionalness) -> major
    for name, np in newp.items():
        if name in oldp:
            op = oldp[name]
            if op.kind != np.kind and (
                op.kind in ("posonly", "pos", "kwonly") or np.kind in ("posonly", "pos", "kwonly")
            ):
                impacts.append(Impact("major", old.fullname, f"Param '{name}' kind changed {op.kind}→{np.kind}"))

    # Added optional param -> minor
    for name, np in newp.items():
        if name not in oldp and (np.default is not None or np.kind in ("kwonly", "vararg", "varkw")):
            impacts.append(Impact("minor", old.fullname, f"Added optional param '{name}'"))

    # Return annotation change -> configurable severity
    if old.returns != new.returns:
        impacts.append(Impact(return_type_change, old.fullname, "Return annotation changed"))

    return impacts

def diff_public_api(old: PublicAPI, new: PublicAPI, return_type_change: str = "minor") -> List[Impact]:
    impacts: List[Impact] = []

    # Removed symbols
    for k in old.keys() - new.keys():
        impacts.append(Impact("major", k, "Removed public symbol"))

    # Surviving symbols
    for k in old.keys() & new.keys():
        impacts.extend(compare_funcs(old[k], new[k], return_type_change=return_type_change))

    # Added symbols
    for k in new.keys() - old.keys():
        impacts.append(Impact("minor", k, "Added public symbol"))

    return impacts

def decide_bump(impacts: List[Impact]) -> str:
    if any(i.severity == "major" for i in impacts):
        return "major"
    if any(i.severity == "minor" for i in impacts):
        return "minor"
    return "patch"
