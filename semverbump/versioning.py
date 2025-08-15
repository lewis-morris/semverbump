"""Helpers for reading and bumping package versions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

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


def read_project_version(
    pyproject_path: str | Path = "pyproject.toml",
    source: Literal["project", "tool.poetry"] = "project",
) -> str:
    """Read the project version from a ``pyproject.toml`` file.

    Args:
        pyproject_path: Path to the ``pyproject.toml`` file.
        source: Metadata table to read the version from.

    Returns:
        Project version string.

    Raises:
        KeyError: If the version field is missing or unsupported.
        ValueError: If ``source`` is unknown.
    """

    data = toml_parse(Path(pyproject_path).read_text(encoding="utf-8"))

    if source == "project":
        proj = data.get("project", {})
        v = proj.get("version")
        if isinstance(v, dict) and "attr" in v:
            raise KeyError("project.version uses attr; unsupported")
        if "dynamic" in proj and "version" in proj.get("dynamic", []):
            raise KeyError("project.version declared dynamic; unsupported")
        if v is not None:
            return str(v)
        if data.get("tool", {}).get("poetry", {}).get("version"):
            raise KeyError("use source='tool.poetry' for poetry-managed version")
        raise KeyError("project.version not found in pyproject.toml")

    if source == "tool.poetry":
        poetry = data.get("tool", {}).get("poetry", {})
        v = poetry.get("version")
        if v is not None:
            return str(v)
        proj = data.get("project", {})
        if isinstance(proj.get("version"), dict) and "attr" in proj["version"]:
            raise KeyError("project.version uses attr; unsupported")
        if "dynamic" in proj and "version" in proj.get("dynamic", []):
            raise KeyError("project.version declared dynamic; unsupported")
        if proj.get("version"):
            raise KeyError("use source='project' for project.version")
        raise KeyError("tool.poetry.version not found in pyproject.toml")

    raise ValueError(f"Unknown source {source}")


def write_project_version(
    new_version: str,
    pyproject_path: str | Path = "pyproject.toml",
    source: Literal["project", "tool.poetry"] = "project",
) -> None:
    """Write ``new_version`` to the ``pyproject.toml`` file.

    Args:
        new_version: Version string to write.
        pyproject_path: Path to the ``pyproject.toml`` file.
        source: Metadata table to update.

    Raises:
        KeyError: If the table is missing or version is unsupported.
        ValueError: If ``source`` is unknown.
    """

    p = Path(pyproject_path)
    data = toml_parse(p.read_text(encoding="utf-8"))
    if source == "project":
        if "project" not in data:
            raise KeyError("No [project] table in pyproject.toml")
        proj = data["project"]
        if isinstance(proj.get("version"), dict) and "attr" in proj["version"]:
            raise KeyError("project.version uses attr; unsupported")
        if "dynamic" in proj and "version" in proj.get("dynamic", []):
            raise KeyError("project.version declared dynamic; unsupported")
        proj["version"] = new_version
    elif source == "tool.poetry":
        tool = data.setdefault("tool", {})
        poetry = tool.get("poetry")
        if poetry is None:
            raise KeyError("No [tool.poetry] table in pyproject.toml")
        poetry["version"] = new_version
    else:
        raise ValueError(f"Unknown source {source}")
    p.write_text(toml_dumps(data), encoding="utf-8")


def apply_bump(
    level: str,
    pyproject_path: str | Path = "pyproject.toml",
    source: Literal["project", "tool.poetry"] = "project",
) -> VersionChange:
    """Apply a semantic version bump to ``pyproject.toml``.

    Args:
        level: Bump level to apply (``"major"``, ``"minor"``, or ``"patch"``).
        pyproject_path: Path to the ``pyproject.toml`` file.
        source: Metadata table holding the version.

    Returns:
        :class:`VersionChange` detailing the old and new versions.
    """

    old = read_project_version(pyproject_path, source=source)
    new = bump_string(old, level)
    write_project_version(new, pyproject_path, source=source)
    return VersionChange(old=old, new=new, level=level)
