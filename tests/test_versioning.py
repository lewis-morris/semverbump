from pathlib import Path

import pytest
from tomlkit import dumps as toml_dumps

from semverbump.versioning import apply_bump, bump_string, read_project_version


def test_bump_string():
    assert bump_string("1.2.3", "patch") == "1.2.4"
    assert bump_string("1.2.3", "minor") == "1.3.0"
    assert bump_string("1.2.3", "major") == "2.0.0"


def test_apply_bump(tmp_path: Path):
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "0.1.0"}}))
    out = apply_bump("minor", py)
    assert out.old == "0.1.0" and out.new == "0.2.0"
    assert read_project_version(py) == "0.2.0"


def test_apply_bump_poetry(tmp_path: Path):
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"tool": {"poetry": {"version": "1.0.0"}}}))
    out = apply_bump("patch", py, source="tool.poetry")
    assert out.old == "1.0.0" and out.new == "1.0.1"
    assert read_project_version(py, source="tool.poetry") == "1.0.1"


def test_read_project_version_dynamic(tmp_path: Path):
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"dynamic": ["version"]}}))
    with pytest.raises(KeyError):
        read_project_version(py)


def test_read_project_version_attr(tmp_path: Path):
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": {"attr": "pkg.__version__"}}}))
    with pytest.raises(KeyError):
        read_project_version(py)
