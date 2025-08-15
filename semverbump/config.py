"""Load and represent ``semverbump`` configuration files."""

from __future__ import annotations

try:  # pragma: no cover - exercised in Python <3.11 tests
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

_DEFAULTS = {
    "project": {
        "package": "",
        "public_roots": ["."],
        "index_file": "pyproject.toml",
        "version_files": [],
    },
    "ignore": {"paths": ["tests/**", "examples/**", "scripts/**"]},
    "rules": {"return_type_change": "minor"},  # or "major"
    "analyzers": {"cli": False},
    "migrations": {"paths": ["migrations"]},
}


@dataclass
class Rules:
    """Rules controlling version bump decisions."""

    return_type_change: str = "minor"  # "minor" | "major"


@dataclass
class Project:
    """Project metadata and locations.

    Attributes:
        package: Importable package name whose ``__init__`` module holds
            ``__version__``.
        public_roots: Roots to scan for public API extraction.
        index_file: Path to the ``pyproject.toml`` file.
        version_files: Additional files containing the project version that
            should be kept in sync when bumping.
    """

    package: str = ""
    public_roots: List[str] = field(default_factory=lambda: ["."])
    index_file: str = "pyproject.toml"
    version_files: List[str] = field(default_factory=list)


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
class Config:
    """Top-level configuration for semverbump.

    Attributes:
        project: Project settings.
        rules: Rules controlling version bumps.
        ignore: Paths to exclude when scanning.
        analyzers: Optional analyzer plugin settings.
    """

    project: Project = field(default_factory=Project)
    rules: Rules = field(default_factory=Rules)
    ignore: Ignore = field(default_factory=Ignore)
    analyzers: Analyzers = field(default_factory=Analyzers)
    migrations: Migrations = field(default_factory=Migrations)


def _merge_defaults(data: dict) -> dict:
    """Merge user data with default configuration."""
    out = {k: dict(v) for k, v in _DEFAULTS.items()}
    for section, content in (data or {}).items():
        out.setdefault(section, {}).update(content or {})
    return out


def load_config(path: str | Path = "semverbump.toml") -> Config:
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
    enabled = {name for name, enabled in d["analyzers"].items() if enabled}
    analyzers = Analyzers(enabled=enabled)
    migrations = Migrations(**d.get("migrations", {}))
    return Config(
        project=proj,
        rules=rules,
        ignore=ign,
        analyzers=analyzers,
        migrations=migrations,
    )
