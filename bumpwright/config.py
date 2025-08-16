"""Load and represent ``bumpwright`` configuration files."""

from __future__ import annotations

try:  # pragma: no cover - exercised in Python <3.11 tests
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib
import copy
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULTS = {
    "project": {"package": "", "public_roots": ["."], "index_file": "pyproject.toml"},
    "ignore": {"paths": ["tests/**", "examples/**", "scripts/**"]},
    "rules": {"return_type_change": "minor"},  # or "major"
    "analysers": {"cli": False},
    "migrations": {"paths": ["migrations"]},
    "changelog": {"path": ""},
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
    public_roots: list[str] = field(default_factory=lambda: ["."])
    index_file: str = "pyproject.toml"


@dataclass
class Ignore:
    """Paths to ignore during scanning."""

    paths: list[str] = field(
        default_factory=lambda: ["tests/**", "examples/**", "scripts/**"]
    )


@dataclass
class Analysers:
    """Analyser plugin configuration.

    Attributes:
        enabled: Names of enabled analyser plugins.
    """

    enabled: set[str] = field(default_factory=set)


@dataclass
class Migrations:
    """Settings for the migrations analyser."""

    paths: list[str] = field(default_factory=lambda: ["migrations"])


@dataclass
class Changelog:
    """Changelog file configuration.

    Attributes:
        path: Default changelog file path. Empty string disables changelog generation.
    """

    path: str = ""


@dataclass
class VersionFiles:
    """Locations containing project version strings.

    Attributes:
        paths: Glob patterns to search for version declarations.
        ignore: Glob patterns to skip during version replacement.
    """

    paths: list[str] = field(
        default_factory=lambda: [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "**/__init__.py",
            "**/version.py",
            "**/_version.py",
        ]
    )
    ignore: list[str] = field(default_factory=list)


@dataclass
class Config:
    """Top-level configuration for bumpwright.

    Attributes:
        project: Project settings.
        rules: Rules controlling version bumps.
        ignore: Paths to exclude when scanning.
        analysers: Optional analyser plugin settings.
        changelog: Default changelog file location.
        version: Locations containing version strings.
    """

    project: Project = field(default_factory=Project)
    rules: Rules = field(default_factory=Rules)
    ignore: Ignore = field(default_factory=Ignore)
    analysers: Analysers = field(default_factory=Analysers)
    migrations: Migrations = field(default_factory=Migrations)
    changelog: Changelog = field(default_factory=Changelog)
    version: VersionFiles = field(default_factory=VersionFiles)


def _merge_defaults(data: dict | None) -> dict:
    """Merge user configuration with built-in defaults.

    Args:
        data: Raw configuration mapping or ``None`` for no user overrides.

    Returns:
        Combined configuration with defaults applied.
    """

    out = copy.deepcopy(_DEFAULTS)  # Deep clone to avoid shared mutable defaults.
    for section, content in (data or {}).items():
        out.setdefault(section, {}).update(content or {})
    return out


def load_config(path: str | Path = "bumpwright.toml") -> Config:
    """Load configuration from a TOML file.

    Args:
        path: Path to the configuration file.

    Returns:
        Parsed configuration object.
    """
    p = Path(path)
    if not p.exists():
        d = _merge_defaults({})
    else:
        d = _merge_defaults(tomllib.loads(p.read_text(encoding="utf-8")))
    proj = Project(**d["project"])
    rules = Rules(**d["rules"])
    ign = Ignore(**d["ignore"])
    enabled = {name for name, enabled in d["analysers"].items() if enabled}
    analysers = Analysers(enabled=enabled)
    migrations = Migrations(**d.get("migrations", {}))
    changelog = Changelog(**d.get("changelog", {}))
    version = VersionFiles(**d.get("version", {}))
    return Config(
        project=proj,
        rules=rules,
        ignore=ign,
        analysers=analysers,
        migrations=migrations,
        changelog=changelog,
        version=version,
    )
