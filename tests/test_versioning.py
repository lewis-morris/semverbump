from pathlib import Path

from tomlkit import dumps as toml_dumps

from semverbump.versioning import apply_bump, bump_string, read_project_version


def test_bump_string():
    assert bump_string("1.2.3", "patch") == "1.2.4"
    assert bump_string("1.2.3", "minor") == "1.3.0"
    assert bump_string("1.2.3", "major") == "2.0.0"


def test_apply_bump(tmp_path: Path) -> None:
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "0.1.0"}}))

    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    init = pkg / "__init__.py"
    init.write_text("__version__ = '0.1.0'")

    extra = tmp_path / "setup.py"
    extra.write_text("version='0.1.0'")

    docs = tmp_path / "docs"
    docs.mkdir()
    conf = docs / "conf.py"
    conf.write_text("release = '0.1.0'")

    out = apply_bump(
        "minor",
        py,
        package="mypkg",
        extra_files=[extra, conf],
    )

    assert out.old == "0.1.0" and out.new == "0.2.0"
    assert read_project_version(py) == "0.2.0"
    for f in (init, extra, conf):
        assert "0.2.0" in f.read_text()
