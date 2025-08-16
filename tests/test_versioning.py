from pathlib import Path

import pytest
from tomlkit import dumps as toml_dumps
from tomlkit.exceptions import ParseError

from bumpwright.versioning import apply_bump, bump_string, read_project_version


def test_bump_string():
    assert bump_string("1.2.3", "patch") == "1.2.4"
    assert bump_string("1.2.3", "minor") == "1.3.0"
    assert bump_string("1.2.3", "major") == "2.0.0"


@pytest.mark.parametrize("level", ["", "foo", "majority"])
def test_bump_string_invalid_level(level: str) -> None:
    """Ensure ``bump_string`` rejects unsupported bump levels."""

    with pytest.raises(ValueError):
        bump_string("1.2.3", level)  # type: ignore[arg-type]


@pytest.fixture
def missing_file(tmp_path: Path) -> Path:
    """Return a path to a non-existent ``pyproject.toml`` file."""

    return tmp_path / "pyproject.toml"


@pytest.fixture
def pyproject_missing_version(tmp_path: Path) -> Path:
    """Create a ``pyproject.toml`` lacking the version field."""

    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {}}))
    return py


@pytest.fixture
def pyproject_malformed(tmp_path: Path) -> Path:
    """Create a malformed ``pyproject.toml`` to trigger parse errors."""

    py = tmp_path / "pyproject.toml"
    py.write_text("::invalid::", encoding="utf-8")
    return py


@pytest.mark.parametrize(
    ("path_fixture", "exc"),
    [
        ("missing_file", FileNotFoundError),
        ("pyproject_missing_version", KeyError),
        ("pyproject_malformed", ParseError),
    ],
)
def test_read_project_version_errors(
    path_fixture: str, exc: type[Exception], request: pytest.FixtureRequest
) -> None:
    """Validate ``read_project_version`` error handling for bad inputs."""

    path = request.getfixturevalue(path_fixture)
    with pytest.raises(exc):
        read_project_version(path)


def test_apply_bump(tmp_path: Path):
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "0.1.0"}}))
    out = apply_bump("minor", py)
    assert out.old == "0.1.0" and out.new == "0.2.0"
    assert read_project_version(py) == "0.2.0"
    assert py in out.files


def test_apply_bump_dry_run(tmp_path: Path) -> None:
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "1.2.3"}}))
    out = apply_bump("patch", py, dry_run=True)
    assert out.old == "1.2.3" and out.new == "1.2.4"
    assert read_project_version(py) == "1.2.3"
    assert out.files == []


def test_apply_bump_updates_extra_files(tmp_path: Path) -> None:
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "0.1.0"}}))
    setup = tmp_path / "setup.py"
    setup.write_text("version='0.1.0'", encoding="utf-8")
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    init = pkg / "__init__.py"
    init.write_text("__version__ = '0.1.0'", encoding="utf-8")
    ver = pkg / "version.py"
    ver.write_text("VERSION = '0.1.0'", encoding="utf-8")
    _ver = pkg / "_version.py"
    _ver.write_text("version = '0.1.0'", encoding="utf-8")

    out = apply_bump("patch", py)
    assert out.new == "0.1.1"
    assert "version='0.1.1'" in setup.read_text(encoding="utf-8")
    assert "__version__ = '0.1.1'" in init.read_text(encoding="utf-8")
    assert "VERSION = '0.1.1'" in ver.read_text(encoding="utf-8")
    assert "version = '0.1.1'" in _ver.read_text(encoding="utf-8")
    # Out files are sorted for deterministic order.
    assert out.files == [py, init, _ver, ver, setup]


def test_apply_bump_ignore_patterns(tmp_path: Path) -> None:
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "1.0.0"}}))
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    init = pkg / "__init__.py"
    init.write_text("__version__ = '1.0.0'", encoding="utf-8")

    out = apply_bump("minor", py, ignore=[str(init)])
    assert "__version__ = '1.0.0'" in init.read_text(encoding="utf-8")
    assert init not in out.files
