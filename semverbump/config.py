from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set
import tomllib

_DEFAULTS = {
    "project": {"package": "", "public_roots": ["."], "index_file": "pyproject.toml"},
    "ignore": {"paths": ["tests/**", "examples/**", "scripts/**"]},
    "rules": {"return_type_change": "minor"},  # or "major"
}

@dataclass
class Rules:
    return_type_change: str = "minor"  # "minor" | "major"

@dataclass
class Project:
    package: str = ""
    public_roots: List[str] = field(default_factory=lambda: ["."])
    index_file: str = "pyproject.toml"

@dataclass
class Ignore:
    paths: List[str] = field(default_factory=lambda: ["tests/**", "examples/**", "scripts/**"])

@dataclass
class Config:
    project: Project = field(default_factory=Project)
    rules: Rules = field(default_factory=Rules)
    ignore: Ignore = field(default_factory=Ignore)

def _merge_defaults(data: dict) -> dict:
    out = {k: dict(v) for k, v in _DEFAULTS.items()}
    for section, content in (data or {}).items():
        out.setdefault(section, {}).update(content or {})
    return out

def load_config(path: str | Path = "semverbump.toml") -> Config:
    p = Path(path)
    if not p.exists():
        d = _merge_defaults({})
    else:
        d = _merge_defaults(tomllib.loads(p.read_text()))
    proj = Project(**d["project"])
    rules = Rules(**d["rules"])
    ign = Ignore(**d["ignore"])
    return Config(project=proj, rules=rules, ignore=ign)
