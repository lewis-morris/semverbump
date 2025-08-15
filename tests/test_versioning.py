from pathlib import Path

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


def test_apply_bump_dry_run(tmp_path: Path) -> None:
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "1.2.3"}}))
    out = apply_bump("patch", py, dry_run=True)
    assert out.old == "1.2.3" and out.new == "1.2.4"
    assert read_project_version(py) == "1.2.3"
