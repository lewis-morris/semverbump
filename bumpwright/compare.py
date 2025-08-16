"""Compare public API definitions and suggest version bumps."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .public_api import FuncSig, Param, PublicAPI
from .types import BumpLevel

# Severity levels for public API changes
Severity = BumpLevel


@dataclass(frozen=True)
class Impact:
    """Describe a change in the public API.

    Attributes:
        severity: Change level (``"major"``, ``"minor"``, or ``"patch"``).
        symbol: Qualified name of the affected symbol.
        reason: Human-friendly explanation of the change.
    """

    severity: Severity
    symbol: str
    reason: str


@dataclass(frozen=True)
class Decision:
    """Describe the outcome of a bump decision.

    Attributes:
        level: Suggested semantic version bump (``"major"``, ``"minor"``,
            ``"patch"``) or ``None`` when no change is required.
        confidence: Proportion of impacts that triggered ``level``.
        reasons: Explanations from :class:`Impact` entries supporting the
            decision.
    """

    level: Severity | None
    confidence: float
    reasons: list[str]


def _index_params(sig: FuncSig) -> dict[str, Param]:
    """Map parameter names to parameter objects.

    Args:
        sig: Function signature to index.

    Returns:
        Mapping of parameter name to :class:`Param` instance.
    """

    return {p.name: p for p in sig.params}


def _removed_params(oldp: dict[str, Param], newp: dict[str, Param], fullname: str) -> list[Impact]:
    """Detect removed parameters between two parameter mappings.

    Args:
        oldp: Parameters from the original function signature indexed by name.
        newp: Parameters from the updated function signature indexed by name.
        fullname: Fully qualified name of the function for reporting.

    Returns:
        List of :class:`Impact` instances describing removed parameters.
    """

    impacts: list[Impact] = []
    for name, op in oldp.items():
        if name not in newp:
            if op.kind in ("posonly", "pos", "kwonly") and op.default is None:
                impacts.append(Impact("major", fullname, f"Removed required param '{name}'"))
            elif op.default is not None or op.kind in ("kwonly", "vararg", "varkw"):
                impacts.append(Impact("minor", fullname, f"Removed optional param '{name}'"))
    return impacts


def _added_params(oldp: dict[str, Param], newp: dict[str, Param], fullname: str) -> list[Impact]:
    """Detect added parameters between two parameter mappings.

    Args:
        oldp: Parameters from the original function signature indexed by name.
        newp: Parameters from the updated function signature indexed by name.
        fullname: Fully qualified name of the function for reporting.

    Returns:
        List of :class:`Impact` instances describing added parameters.
    """

    impacts: list[Impact] = []
    for name, np in newp.items():
        if name not in oldp:
            if np.default is None and np.kind in ("posonly", "pos", "kwonly"):
                impacts.append(Impact("major", fullname, f"Added required param '{name}'"))
            else:
                impacts.append(Impact("minor", fullname, f"Added optional param '{name}'"))
    return impacts


def _param_kind_changes(oldp: dict[str, Param], newp: dict[str, Param], fullname: str) -> list[Impact]:
    """Detect changes in parameter kind between two parameter mappings.

    Args:
        oldp: Parameters from the original function signature indexed by name.
        newp: Parameters from the updated function signature indexed by name.
        fullname: Fully qualified name of the function for reporting.

    Returns:
        List of :class:`Impact` instances describing kind changes.
    """

    impacts: list[Impact] = []
    for name, np in newp.items():
        if name in oldp:
            op = oldp[name]
            if op.kind != np.kind and (op.kind in ("posonly", "pos", "kwonly") or np.kind in ("posonly", "pos", "kwonly")):
                impacts.append(
                    Impact(
                        "major",
                        fullname,
                        f"Param '{name}' kind changed {op.kind}→{np.kind}",
                    )
                )
    return impacts


def _param_default_changes(oldp: dict[str, Param], newp: dict[str, Param], fullname: str) -> list[Impact]:
    """Detect parameter default value changes between two mappings.

    Args:
        oldp: Parameters from the original function signature indexed by name.
        newp: Parameters from the updated function signature indexed by name.
        fullname: Fully qualified name of the function for reporting.

    Returns:
        List of :class:`Impact` instances describing default value changes.
    """

    impacts: list[Impact] = []
    for name, np in newp.items():
        if name in oldp:
            op = oldp[name]
            if op.default != np.default:
                if op.default is None and np.default is not None:
                    impacts.append(Impact("minor", fullname, f"Param '{name}' default added"))
                elif op.default is not None and np.default is None:
                    impacts.append(Impact("major", fullname, f"Param '{name}' default removed"))
                else:
                    impacts.append(
                        Impact(
                            "minor",
                            fullname,
                            f"Param '{name}' default changed {op.default}→{np.default}",
                        )
                    )
    return impacts


def _param_annotation_changes(
    oldp: dict[str, Param],
    newp: dict[str, Param],
    fullname: str,
    severity: Severity,
) -> list[Impact]:
    """Detect parameter annotation changes between two mappings.

    Args:
        oldp: Parameters from the original function signature indexed by name.
        newp: Parameters from the updated function signature indexed by name.
        fullname: Fully qualified name of the function for reporting.
        severity: Impact level for annotation changes.

    Returns:
        List of :class:`Impact` instances describing annotation changes.
    """

    impacts: list[Impact] = []
    for name, np in newp.items():
        if name in oldp:
            op = oldp[name]
            if op.annotation != np.annotation:
                if op.annotation is None and np.annotation is not None:
                    reason = f"Param '{name}' annotation added"
                elif op.annotation is not None and np.annotation is None:
                    reason = f"Param '{name}' annotation removed"
                else:
                    reason = f"Param '{name}' annotation changed {op.annotation}→{np.annotation}"
                impacts.append(Impact(severity, fullname, reason))
    return impacts


def _return_annotation_change(old: FuncSig, new: FuncSig, severity: Severity) -> list[Impact]:
    """Detect return annotation change between two signatures.

    Args:
        old: Original function signature.
        new: Updated function signature.
        severity: Impact level to report when the return annotation changes.

    Returns:
        A list containing a single :class:`Impact` if the return annotation
        changed, otherwise an empty list.
    """

    if old.returns != new.returns:
        return [Impact(severity, old.fullname, "Return annotation changed")]
    return []


def compare_funcs(
    old: FuncSig,
    new: FuncSig,
    return_type_change: Severity = "minor",
    param_annotation_change: Severity = "patch",
) -> list[Impact]:
    """Compare two function signatures and record API impacts.

    Args:
        old: Original function signature.
        new: Updated function signature.
        return_type_change: Severity level for return type changes.
        param_annotation_change: Severity level for parameter annotation changes.

    Returns:
        List of :class:`Impact` instances describing detected changes.
    """

    oldp = _index_params(old)
    newp = _index_params(new)

    impacts = (
        _removed_params(oldp, newp, old.fullname)
        + _param_kind_changes(oldp, newp, old.fullname)
        + _param_default_changes(oldp, newp, old.fullname)
        + _param_annotation_changes(oldp, newp, old.fullname, param_annotation_change)
        + _added_params(oldp, newp, old.fullname)
        + _return_annotation_change(old, new, return_type_change)
    )

    return impacts


def diff_public_api(
    old: PublicAPI,
    new: PublicAPI,
    return_type_change: Severity = "minor",
    param_annotation_change: Severity = "patch",
) -> list[Impact]:
    """Compute impacts between two public API mappings.

    Args:
        old: Mapping of symbols to signatures for the base reference.
        new: Mapping of symbols to signatures for the head reference.
        return_type_change: Severity level for return type changes.
        param_annotation_change: Severity level for parameter annotation changes.

    Returns:
        List of detected impacts.
    """

    impacts: list[Impact] = []

    # Removed symbols
    for k in old.keys() - new.keys():
        impacts.append(Impact("major", k, "Removed public symbol"))

    # Surviving symbols
    for k in old.keys() & new.keys():
        impacts.extend(
            compare_funcs(
                old[k],
                new[k],
                return_type_change=return_type_change,
                param_annotation_change=param_annotation_change,
            )
        )

    # Added symbols
    for k in new.keys() - old.keys():
        impacts.append(Impact("minor", k, "Added public symbol"))

    return impacts


def decide_bump(impacts: list[Impact]) -> Decision:
    """Determine the bump level from a list of impacts.

    Args:
        impacts: Detected impacts from API comparison.

    Returns:
        Decision detailing the suggested bump level, confidence and reasons.
    """

    if not impacts:
        return Decision(None, 0.0, [])

    counts: Counter[Severity] = Counter(i.severity for i in impacts)
    total = sum(counts.values())
    if counts.get("major"):
        level: Severity = "major"
    elif counts.get("minor"):
        level = "minor"
    else:
        level = "patch"
    level_count = counts.get(level, 0)
    reasons = [i.reason for i in impacts if i.severity == level]
    confidence = level_count / total if total else 0.0
    return Decision(level, confidence, reasons)
