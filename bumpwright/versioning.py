"""Utilities to read and bump project version numbers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from fnmatch import fnmatch
from functools import lru_cache
from glob import glob
from pathlib import Path

from tomlkit import dumps as toml_dumps
from tomlkit import parse as toml_parse

from .config import load_config
from .types import BumpLevel
from .version_schemes import get_version_scheme


@dataclass
class VersionChange:
    """Result of applying a version bump.

    Attributes:
        old: Previous version string.
        new: New version string after bump.
        level: Bump level applied (``"major"``, ``"minor"``, or ``"patch"``).
        files: Files updated with the new version.
    """

    old: str
    new: str
    level: BumpLevel
    files: list[Path] = field(default_factory=list)


def bump_string(v: str, level: BumpLevel, scheme: str | None = None) -> str:
    """Increment ``v`` according to ``level`` using a version scheme.

    Args:
        v: Version string to bump.
        level: Desired bump level.
        scheme: Optional scheme name. When ``None``, the configured scheme from
            ``bumpwright.toml`` is used.

    Returns:
        Bumped version string.

    Raises:
        ValueError: If ``level`` or the scheme name is unsupported.
    """

    scheme_name = scheme or load_config().version.scheme
    impl = get_version_scheme(scheme_name)
    return impl.bump(v, level)


def find_pyproject(start: str | Path | None = None) -> Path | None:
    """Search upward from ``start`` for ``pyproject.toml``.

    Args:
        start: Directory to begin searching from. Defaults to the current working
            directory.

    Returns:
        Path to the discovered ``pyproject.toml`` file, or ``None`` if not found.
    """

    path = Path(start or Path.cwd()).resolve()
    for parent in [path, *path.parents]:
        candidate = parent / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


def read_project_version(pyproject_path: str | Path = "pyproject.toml") -> str:
    """Read the project version from a ``pyproject.toml`` file.

    Args:
        pyproject_path: Path to the ``pyproject.toml`` file.

    Returns:
        Project version string.

    Raises:
        KeyError: If the version field is missing.
    """

    p = Path(pyproject_path)
    if not p.is_file():
        p = find_pyproject(p.parent)
        if p is None:
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
    data = toml_parse(p.read_text(encoding="utf-8"))
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
    if not p.is_file():
        p = find_pyproject(p.parent)
        if p is None:
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
    data = toml_parse(p.read_text(encoding="utf-8"))
    if "project" not in data:
        raise KeyError("No [project] table in pyproject.toml")
    data["project"]["version"] = new_version
    p.write_text(toml_dumps(data), encoding="utf-8")


def apply_bump(  # noqa: PLR0913
    level: BumpLevel,
    pyproject_path: str | Path = "pyproject.toml",
    dry_run: bool = False,
    paths: Iterable[str] | None = None,
    ignore: Iterable[str] | None = None,
    scheme: str | None = None,
) -> VersionChange:
    """Apply a version bump and update version strings.

    Args:
        level: Bump level to apply.
        pyproject_path: Path to the canonical ``pyproject.toml`` file.
        dry_run: If ``True``, compute the new version without writing to disk.
        paths: Glob patterns pointing to files that may contain the version.
            Defaults include ``pyproject.toml``, ``setup.py``, ``setup.cfg`` and
            any ``__init__.py``, ``version.py`` or ``_version.py`` files within
            the project. Custom patterns extend this list.
        ignore: Glob patterns to exclude from ``paths``. Defaults to values from
            the project configuration when ``None``.
        scheme: Versioning scheme identifier. When ``None``, the scheme from
            configuration is used.

    Returns:
        :class:`VersionChange` detailing the old and new versions and updated
        files.

    Notes:
        Resolved file paths are cached across invocations for performance.
        Call ``_resolve_files_cached.cache_clear()`` if the filesystem changes
        and a fresh resolution is required.
    """

    cfg = load_config()
    if paths is None:
        paths = cfg.version.paths
    if ignore is None:
        ignore = cfg.version.ignore
    if scheme is None:
        scheme = cfg.version.scheme

    old = read_project_version(pyproject_path)
    new = bump_string(old, level, scheme)
    if dry_run:
        return VersionChange(old=old, new=new, level=level)

    write_project_version(new, pyproject_path)
    updated = _update_additional_files(new, old, paths, ignore, pyproject_path)
    return VersionChange(
        old=old,
        new=new,
        level=level,
        files=[Path(pyproject_path), *updated],
    )


def _update_additional_files(
    new: str,
    old: str,
    patterns: Iterable[str],
    ignore: Iterable[str],
    pyproject_path: str | Path,
) -> list[Path]:
    """Update version strings in files matching ``patterns``.

    Args:
        new: New version string.
        old: Previous version string.
        patterns: Glob patterns to search for files.
        ignore: Glob patterns to skip.
        pyproject_path: Canonical ``pyproject.toml`` path to skip (already updated).

    Returns:
        List of files that were updated.
    """

    base = Path(pyproject_path).resolve().parent
    files = _resolve_files(patterns, ignore, base)
    canon = Path(pyproject_path).resolve()
    changed: list[Path] = []
    for f in files:
        if f.resolve() == canon:
            continue
        _replace_version(f, old, new)
        changed.append(f)
    return changed


def _resolve_files(
    patterns: Iterable[str], ignore: Iterable[str], base_dir: Path
) -> list[Path]:
    """Expand glob patterns while applying ignore rules relative to ``base_dir``.

    Args:
        patterns: Glob patterns to search for version files.
        ignore: Glob patterns to exclude from results.
        base_dir: Directory relative to which patterns are evaluated.

    Returns:
        List of discovered file paths matching ``patterns`` minus ``ignore``.

    Notes:
        Results are cached based on ``patterns``, ``ignore``, and ``base_dir`` for
        performance.
    """

    base = Path(base_dir).resolve()
    return list(_resolve_files_cached(tuple(patterns), tuple(ignore), str(base)))


@lru_cache(maxsize=None)
def _resolve_files_cached(
    patterns: tuple[str, ...], ignore: tuple[str, ...], base_dir: str
) -> tuple[Path, ...]:
    """Resolve files for caching.

    This function performs the actual glob resolution and is wrapped with
    ``functools.lru_cache`` via :func:`_resolve_files`.

    Args:
        patterns: Glob patterns to search for version files.
        ignore: Glob patterns to exclude from results.
        base_dir: Directory relative to which patterns are evaluated.

    Returns:
        Tuple of discovered file paths matching ``patterns`` minus ``ignore``.
    """

    out: list[Path] = []
    ignore_list = list(ignore)
    base = Path(base_dir)
    for pat in patterns:
        pat_path = Path(pat)
        search = pat if pat_path.is_absolute() else str(base / pat)
        for match in glob(search, recursive=True):
            p = Path(match)
            if not p.is_file():
                continue
            path_str = str(p)
            try:
                rel_str = str(p.resolve().relative_to(base))
            except ValueError:
                rel_str = path_str
            if any(fnmatch(path_str, ig) or fnmatch(rel_str, ig) for ig in ignore_list):
                continue
            out.append(p)
    # Ensure deterministic ordering for predictable downstream operations.
    out.sort()
    return tuple(out)


def _replace_version(path: Path, old: str, new: str) -> None:
    """Replace occurrences of ``old`` version with ``new`` in ``path``.

    Args:
        path: File whose contents should be updated.
        old: Previous version string.
        new: New version string.
    """

    text = path.read_text(encoding="utf-8")
    patterns = [
        rf"(__version__\s*=\s*['\"])({re.escape(old)})(['\"])",
        rf"(VERSION\s*=\s*['\"])({re.escape(old)})(['\"])",
        rf"(version\s*=\s*['\"])({re.escape(old)})(['\"])",
    ]
    for pat in patterns:
        text, _ = re.subn(pat, rf"\g<1>{new}\g<3>", text)
    path.write_text(text, encoding="utf-8")
