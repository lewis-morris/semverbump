"""Load and represent ``bumpwright`` configuration files."""

from __future__ import annotations

try:  # pragma: no cover - exercised in Python <3.11 tests
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Set

_DEFAULTS = {
    "project": {"package": "", "public_roots": ["."], "index_file": "pyproject.toml"},
    "ignore": {"paths": ["tests/**", "examples/**", "scripts/**"]},
    "rules": {"return_type_change": "minor"},  # or "major"
    "analyzers": {"cli": False},
    "migrations": {"paths": ["migrations"]},
    "version": {
        "paths": [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "**/__init__.py",
            "**/version.py",
            "**/_version.py",
        ],
        "ignore": [],
    },
}


@dataclass
class Rules:
    """Rules controlling version bump decisions."""

    return_type_change: str = "minor"  # "minor" | "major"


@dataclass
class Project:
    """Project metadata and locations."""

    package: str = ""
    public_roots: List[str] = field(default_factory=lambda: ["."])
    index_file: str = "pyproject.toml"


@dataclass
class Ignore:
    """Paths to ignore during scanning."""

    paths: List[str] = field(
        default_factory=lambda: ["tests/**", "examples/**", "scripts/**"]
    )


@dataclass
class Analyzers:
    """Analyzer plugin configuration.

    Attributes:
        enabled: Names of enabled analyzer plugins.
    """

    enabled: Set[str] = field(default_factory=set)


@dataclass
class Migrations:
    """Settings for the migrations analyzer."""

    paths: List[str] = field(default_factory=lambda: ["migrations"])


@dataclass
class VersionFiles:
    """Locations containing project version strings.

    Attributes:
        paths: Glob patterns to search for version declarations.
        ignore: Glob patterns to skip during version replacement.
    """

    paths: List[str] = field(
        default_factory=lambda: [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "**/__init__.py",
            "**/version.py",
            "**/_version.py",
        ]
    )
    ignore: List[str] = field(default_factory=list)


@dataclass
class Config:
    """Top-level configuration for bumpwright.

    Attributes:
        project: Project settings.
        rules: Rules controlling version bumps.
        ignore: Paths to exclude when scanning.
        analyzers: Optional analyzer plugin settings.
        version: Locations containing version strings.
    """

    project: Project = field(default_factory=Project)
    rules: Rules = field(default_factory=Rules)
    ignore: Ignore = field(default_factory=Ignore)
    analyzers: Analyzers = field(default_factory=Analyzers)
    migrations: Migrations = field(default_factory=Migrations)
    version: VersionFiles = field(default_factory=VersionFiles)


def _merge_defaults(data: dict | None) -> dict:
    """Merge user configuration with built-in defaults.

    Args:
        data: Raw configuration mapping or ``None`` for no user overrides.

    Returns:
        Combined configuration with defaults applied.
    """

    out = {k: dict(v) for k, v in _DEFAULTS.items()}
    for section, content in (data or {}).items():
        out.setdefault(section, {}).update(content or {})
    return out


def load_config(
    path: str | Path = "bumpwright.toml",
    *,
    enable: Iterable[str] | None = None,
    disable: Iterable[str] | None = None,
) -> Config:
    """Load configuration from a TOML file and apply overrides.

    Args:
        path: Path to the configuration file.
        enable: Analyzer names to force-enable.
        disable: Analyzer names to disable even if configured.

    Returns:
        Parsed configuration object with overrides applied.
    """

    p = Path(path)
    if not p.exists():
        d = _merge_defaults({})
    else:
        d = _merge_defaults(tomllib.loads(p.read_text(encoding="utf-8")))
    proj = Project(**d["project"])
    rules = Rules(**d["rules"])
    ign = Ignore(**d["ignore"])
    enabled = {name for name, enabled in d["analyzers"].items() if enabled}
    if enable:
        enabled.update(enable)
    if disable:
        enabled.difference_update(disable)
    analyzers = Analyzers(enabled=enabled)
    migrations = Migrations(**d.get("migrations", {}))
    version = VersionFiles(**d.get("version", {}))
    return Config(
        project=proj,
        rules=rules,
        ignore=ign,
        analyzers=analyzers,
        migrations=migrations,
        version=version,
    )
