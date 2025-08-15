"""Helpers for reading and bumping package versions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatch
from glob import glob
from pathlib import Path
from typing import Iterable, List

try:  # pragma: no cover - needed for linting when dependency missing
    from packaging.version import Version
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError("packaging is required for version operations") from exc
from tomlkit import dumps as toml_dumps
from tomlkit import parse as toml_parse


@dataclass
class VersionChange:
    """Result of applying a version bump.

    Attributes:
        old: Previous version string.
        new: New version string after bump.
        level: Bump level applied (``"major"``, ``"minor"``, or ``"patch"``).
    """

    old: str
    new: str
    level: str  # "major" | "minor" | "patch"


def bump_string(v: str, level: str) -> str:
    """Increment a semantic version string by ``level``.

    Args:
        v: Version string in ``X.Y.Z`` form.
        level: Bump level (``"major"``, ``"minor"``, or ``"patch"``).

    Returns:
        Bumped version string.

    Raises:
        ValueError: If ``level`` is not one of the supported values.
    """

    pv = Version(v)
    # Only support simple X.Y.Z for now (reject epoch/local/dev)
    parts = [pv.major, pv.minor, pv.micro]
    if level == "major":
        parts = [parts[0] + 1, 0, 0]
    elif level == "minor":
        parts = [parts[0], parts[1] + 1, 0]
    elif level == "patch":
        parts = [parts[0], parts[1], parts[2] + 1]
    else:
        raise ValueError(f"Unknown level {level}")
    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def read_project_version(pyproject_path: str | Path = "pyproject.toml") -> str:
    """Read the project version from a ``pyproject.toml`` file.

    Args:
        pyproject_path: Path to the ``pyproject.toml`` file.

    Returns:
        Project version string.

    Raises:
        KeyError: If the version field is missing.
    """

    data = toml_parse(Path(pyproject_path).read_text(encoding="utf-8"))
    try:
        return str(data["project"]["version"])
    except Exception as e:  # pragma: no cover - explicit re-raise for clarity
        raise KeyError("project.version not found in pyproject.toml") from e


def write_project_version(
    new_version: str, pyproject_path: str | Path = "pyproject.toml"
) -> None:
    """Write ``new_version`` to the ``pyproject.toml`` file.

    Args:
        new_version: Version string to write.
        pyproject_path: Path to the ``pyproject.toml`` file.

    Raises:
        KeyError: If the ``[project]`` table is missing from the file.
    """

    p = Path(pyproject_path)
    data = toml_parse(p.read_text(encoding="utf-8"))
    if "project" not in data:
        raise KeyError("No [project] table in pyproject.toml")
    data["project"]["version"] = new_version
    p.write_text(toml_dumps(data), encoding="utf-8")


def apply_bump(
    level: str,
    pyproject_path: str | Path = "pyproject.toml",
    dry_run: bool = False,
    paths: Iterable[str] | None = None,
    ignore: Iterable[str] | None = None,
) -> VersionChange:
    """Apply a semantic version bump and update version strings.

    Args:
        level: Bump level to apply (``"major"``, ``"minor"``, or ``"patch"``).
        pyproject_path: Path to the canonical ``pyproject.toml`` file.
        dry_run: If ``True``, compute the new version without writing to disk.
        paths: Glob patterns pointing to files that may contain the version.
            The canonical ``pyproject.toml`` is always updated.
        ignore: Glob patterns to exclude from ``paths``.

    Returns:
        :class:`VersionChange` detailing the old and new versions.
    """

    old = read_project_version(pyproject_path)
    new = bump_string(old, level)
    if dry_run:
        return VersionChange(old=old, new=new, level=level)

    write_project_version(new, pyproject_path)
    _update_additional_files(new, old, paths or [], ignore or [], pyproject_path)
    return VersionChange(old=old, new=new, level=level)


def _update_additional_files(
    new: str,
    old: str,
    patterns: Iterable[str],
    ignore: Iterable[str],
    pyproject_path: str | Path,
) -> None:
    """Update version strings in files matching ``patterns``.

    Args:
        new: New version string.
        old: Previous version string.
        patterns: Glob patterns to search for files.
        ignore: Glob patterns to skip.
        pyproject_path: Canonical ``pyproject.toml`` path to skip (already updated).
    """

    files = _resolve_files(patterns, ignore)
    canon = Path(pyproject_path).resolve()
    for f in files:
        if f.resolve() == canon:
            continue
        _replace_version(f, old, new)


def _resolve_files(patterns: Iterable[str], ignore: Iterable[str]) -> List[Path]:
    """Expand glob patterns while applying ignore rules."""

    out: List[Path] = []
    ignore_list = list(ignore)
    for pat in patterns:
        for match in glob(pat, recursive=True):
            p = Path(match)
            if not p.is_file():
                continue
            if any(fnmatch(str(p), ig) for ig in ignore_list):
                continue
            out.append(p)
    return out


def _replace_version(path: Path, old: str, new: str) -> None:
    """Replace occurrences of ``old`` version with ``new`` in ``path``."""

    text = path.read_text(encoding="utf-8")
    patterns = [
        rf"(__version__\s*=\s*['\"])({re.escape(old)})(['\"])",
        rf"(VERSION\s*=\s*['\"])({re.escape(old)})(['\"])",
        rf"(version\s*=\s*['\"])({re.escape(old)})(['\"])",
    ]
    for pat in patterns:
        text, _ = re.subn(pat, rf"\g<1>{new}\g<3>", text)
    path.write_text(text, encoding="utf-8")
