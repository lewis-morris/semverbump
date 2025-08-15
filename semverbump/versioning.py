from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple
from packaging.version import Version
from tomlkit import parse as toml_parse, dumps as toml_dumps

@dataclass
class VersionChange:
    old: str
    new: str
    level: str  # "major" | "minor" | "patch"

def bump_string(v: str, level: str) -> str:
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
    data = toml_parse(Path(pyproject_path).read_text())
    try:
        return str(data["project"]["version"])
    except Exception as e:
        raise KeyError("project.version not found in pyproject.toml") from e

def write_project_version(new_version: str, pyproject_path: str | Path = "pyproject.toml") -> None:
    p = Path(pyproject_path)
    data = toml_parse(p.read_text())
    if "project" not in data:
        raise KeyError("No [project] table in pyproject.toml")
    data["project"]["version"] = new_version
    p.write_text(toml_dumps(data))

def apply_bump(level: str, pyproject_path: str | Path = "pyproject.toml") -> VersionChange:
    old = read_project_version(pyproject_path)
    new = bump_string(old, level)
    write_project_version(new, pyproject_path)
    return VersionChange(old=old, new=new, level=level)
