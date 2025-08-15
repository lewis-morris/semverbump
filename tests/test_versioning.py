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


def test_apply_bump_updates_extra_files(tmp_path: Path) -> None:
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "0.1.0"}}))
    setup = tmp_path / "setup.py"
    setup.write_text("version='0.1.0'", encoding="utf-8")
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    init = pkg / "__init__.py"
    init.write_text("__version__ = '0.1.0'", encoding="utf-8")

    out = apply_bump(
        "patch",
        py,
        paths=[str(py), str(setup), str(init)],
    )
    assert out.new == "0.1.1"
    assert "version='0.1.1'" in setup.read_text(encoding="utf-8")
    assert "__version__ = '0.1.1'" in init.read_text(encoding="utf-8")


def test_apply_bump_ignore_patterns(tmp_path: Path) -> None:
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "1.0.0"}}))
    other = tmp_path / "other.py"
    other.write_text("__version__ = '1.0.0'", encoding="utf-8")

    apply_bump(
        "minor",
        py,
        paths=[str(py), str(other)],
        ignore=[str(other)],
    )
    assert "__version__ = '1.0.0'" in other.read_text(encoding="utf-8")
