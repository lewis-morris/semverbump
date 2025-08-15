"""Minimal TOML parser for tests.

This module provides a tiny subset of the :mod:`tomli` interface used in the
project's test suite. It supports only what the tests require: basic tables and
string or boolean values. The implementation is intentionally simple and does
not aim to be a full TOML parser.
"""

from __future__ import annotations

from typing import Any, Dict


def loads(src: str) -> Dict[str, Any]:
    """Parse a small subset of TOML into a dictionary.

    The parser understands table headers (e.g. ``[section]``) and key-value
    assignments where values are strings or booleans. It ignores blank lines and
    comments beginning with ``#``.

    Args:
        src: TOML document as a string.

    Returns:
        Parsed representation as a nested dictionary.
    """

    result: Dict[str, Any] = {}
    current: Dict[str, Any] = result

    for raw_line in src.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            current = result.setdefault(section, {})
            continue
        if "=" in line:
            key, value = map(str.strip, line.split("=", 1))
            current[key] = _parse_value(value)
    return result


def _parse_value(value: str) -> Any:
    """Parse a primitive TOML value.

    Args:
        value: Raw value string from the TOML document.

    Returns:
        The parsed Python object.

    Raises:
        ValueError: If the value uses an unsupported type.
    """

    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value in {"true", "false"}:
        return value == "true"
    raise ValueError(f"Unsupported value: {value!r}")


__all__ = ["loads"]
