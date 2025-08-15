"""Minimal TOML helpers implementing a subset of :mod:`tomlkit`.

Only the small surface area required by the tests is provided: ``parse`` for
loading TOML strings and ``dumps`` for serialising simple dictionaries back to
TOML. The implementation intentionally supports only the features exercised in
the tests and is not a general replacement for :mod:`tomlkit`.
"""

from __future__ import annotations

import tomllib
from typing import Any, Dict


def parse(text: str) -> Dict[str, Any]:
    """Parse ``text`` as TOML using :mod:`tomllib`.

    Args:
        text: TOML document.

    Returns:
        Parsed document as a nested dictionary.
    """

    return tomllib.loads(text)


def dumps(data: Dict[str, Any]) -> str:
    """Serialise ``data`` to TOML.

    Only supports dictionaries containing nested dictionaries with string
    values. This limitation keeps the implementation lightweight while still
    satisfying the test-suite requirements.
    """

    lines: list[str] = []
    for section, content in data.items():
        lines.append(f"[{section}]")
        for key, value in content.items():
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:  # pragma: no cover - defensive programming
                raise TypeError("Unsupported value type for minimal TOML writer")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["parse", "dumps"]
