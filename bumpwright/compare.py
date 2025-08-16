"""Compare public API definitions and suggest version bumps."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .public_api import FuncSig, Param, PublicAPI


@dataclass(frozen=True)
class Impact:
    """Describe a change in the public API.

    Attributes:
        severity: Change level (``"major"``, ``"minor"``, or ``"patch"``).
        symbol: Qualified name of the affected symbol.
        reason: Human-friendly explanation of the change.
    """

    severity: str  # "major" | "minor" | "patch"
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

    level: str | None
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


def compare_funcs(
    old: FuncSig, new: FuncSig, return_type_change: str = "minor"
) -> list[Impact]:
    """Compare two function signatures and record API impacts.

    Args:
        old: Original function signature.
        new: Updated function signature.
        return_type_change: Severity level for return type changes.

    Returns:
        List of :class:`Impact` instances describing detected changes.
    """

    impacts: list[Impact] = []

    oldp = _index_params(old)
    newp = _index_params(new)

    # Removed parameters
    for name, op in oldp.items():
        if name not in newp:
            if op.kind in ("posonly", "pos", "kwonly") and op.default is None:
                impacts.append(
                    Impact("major", old.fullname, f"Removed required param '{name}'")
                )
            elif op.default is not None or op.kind in (
                "kwonly",
                "vararg",
                "varkw",
            ):
                impacts.append(
                    Impact("minor", old.fullname, f"Removed optional param '{name}'")
                )

    # Param kind changes are major; added params are major if required otherwise minor
    for name, np in newp.items():
        if name in oldp:
            op = oldp[name]
            if op.kind != np.kind and (
                op.kind in ("posonly", "pos", "kwonly")
                or np.kind in ("posonly", "pos", "kwonly")
            ):
                impacts.append(
                    Impact(
                        "major",
                        old.fullname,
                        f"Param '{name}' kind changed {op.kind}→{np.kind}",
                    )
                )
        else:
            if np.default is None and np.kind in ("posonly", "pos", "kwonly"):
                impacts.append(
                    Impact("major", old.fullname, f"Added required param '{name}'")
                )
            else:
                impacts.append(
                    Impact("minor", old.fullname, f"Added optional param '{name}'")
                )

    # Return annotation change -> configurable severity
    if old.returns != new.returns:
        impacts.append(
            Impact(return_type_change, old.fullname, "Return annotation changed")
        )

    return impacts


def diff_public_api(
    old: PublicAPI, new: PublicAPI, return_type_change: str = "minor"
) -> list[Impact]:
    """Compute impacts between two public API mappings.

    Args:
        old: Mapping of symbols to signatures for the base reference.
        new: Mapping of symbols to signatures for the head reference.
        return_type_change: Severity level for return type changes.

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
            compare_funcs(old[k], new[k], return_type_change=return_type_change)
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

    counts = Counter(i.severity for i in impacts)
    total = sum(counts.values())
    if counts.get("major"):
        level = "major"
    elif counts.get("minor"):
        level = "minor"
    else:
        level = "patch"
    level_count = counts.get(level, 0)
    reasons = [i.reason for i in impacts if i.severity == level]
    confidence = level_count / total if total else 0.0
    return Decision(level, confidence, reasons)
