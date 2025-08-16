from pathlib import Path

import pytest
from tomlkit import dumps as toml_dumps
from tomlkit.exceptions import ParseError

from bumpwright.versioning import (
    _resolve_files,
    _resolve_files_cached,
    apply_bump,
    bump_string,
    find_pyproject,
    read_project_version,
    write_project_version,
)


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


def test_apply_bump_respects_scheme(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use configured version scheme when bumping."""

    (tmp_path / "bumpwright.toml").write_text("[version]\nscheme='pep440'\n")
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "1!1.0.0"}}))
    monkeypatch.chdir(tmp_path)
    out = apply_bump("patch", py)
    assert out.new == "1!1.0.1"


def test_apply_bump_invalid_scheme(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid version schemes raise clear errors."""

    (tmp_path / "bumpwright.toml").write_text("[version]\nscheme='unknown'\n")
    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "0.1.0"}}))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="Unknown version scheme"):
        apply_bump("patch", py)


def test_resolve_files_nested_dirs_sorted(tmp_path: Path) -> None:
    """Resolve nested patterns and ensure results are deterministically ordered."""

    pkg = tmp_path / "pkg"
    sub = pkg / "sub"
    sub.mkdir(parents=True)

    # Create files in non-sorted order to verify output sorting.
    paths = [
        pkg / "b.txt",
        pkg / "a.txt",
        sub / "d.txt",
        sub / "c.txt",
    ]
    for path in paths:
        path.write_text("", encoding="utf-8")

    out = _resolve_files(["pkg/**/*.txt"], [], tmp_path)
    expected = [
        pkg / "a.txt",
        pkg / "b.txt",
        sub / "c.txt",
        sub / "d.txt",
    ]
    assert out == expected


def test_resolve_files_absolute_paths_and_ignore_patterns(tmp_path: Path) -> None:
    """Handle absolute patterns and exclusion rules in file resolution."""

    base = tmp_path
    abs_file = base / "abs.py"
    abs_file.write_text("", encoding="utf-8")

    ignore_abs = base / "ignore_abs.py"
    ignore_abs.write_text("", encoding="utf-8")

    pkg = base / "pkg"
    pkg.mkdir()
    keep_rel = pkg / "keep.py"
    keep_rel.write_text("", encoding="utf-8")
    ignore_rel = pkg / "ignore_rel.py"
    ignore_rel.write_text("", encoding="utf-8")

    patterns = [str(abs_file), str(ignore_abs), "pkg/*.py"]
    ignore = [str(ignore_abs), "pkg/ignore_rel.py"]
    out = _resolve_files(patterns, ignore, base)
    expected = [abs_file, keep_rel]
    assert out == expected


def test_resolve_files_uses_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ensure repeated resolution reuses cached results."""

    (tmp_path / "a.txt").write_text("1", encoding="utf-8")
    (tmp_path / "b.txt").write_text("2", encoding="utf-8")
    _resolve_files_cached.cache_clear()
    calls = {"count": 0}
    from bumpwright.versioning import glob as glob_orig  # noqa: PLC0415

    def fake_glob(pattern: str, recursive: bool = True) -> list[str]:
        calls["count"] += 1
        return glob_orig(pattern, recursive=recursive)

    monkeypatch.setattr("bumpwright.versioning.glob", fake_glob)
    _resolve_files(["*.txt"], [], tmp_path)
    _resolve_files(["*.txt"], [], tmp_path)
    assert calls["count"] == 1


def test_apply_bump_clears_resolve_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify custom patterns trigger cache invalidation."""

    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "0.1.0"}}))
    cfg = tmp_path / "extra.cfg"
    cfg.write_text("version = '0.1.0'", encoding="utf-8")

    calls = {"count": 0}
    from bumpwright.versioning import glob as glob_orig  # noqa: PLC0415

    def fake_glob(pattern: str, recursive: bool = True) -> list[str]:
        calls["count"] += 1
        return glob_orig(pattern, recursive=recursive)

    monkeypatch.setattr("bumpwright.versioning.glob", fake_glob)
    apply_bump("patch", py, paths=["*.cfg"])
    apply_bump("patch", py, paths=["*.cfg"])
    assert calls["count"] == 1


def test_find_pyproject(tmp_path: Path) -> None:
    """Locate the nearest ``pyproject.toml`` when present."""

    root = tmp_path / "proj"
    root.mkdir()
    py = root / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "0.1.0"}}))
    sub = root / "pkg"
    sub.mkdir()
    assert find_pyproject(sub) == py


def test_find_pyproject_missing(tmp_path: Path) -> None:
    """Return ``None`` when no ``pyproject.toml`` is found."""

    assert find_pyproject(tmp_path / "missing") is None


def test_write_project_version(tmp_path: Path) -> None:
    """Update the project version in ``pyproject.toml``."""

    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({"project": {"version": "0.1.0"}}))
    write_project_version("0.2.0", py)
    assert read_project_version(py) == "0.2.0"


def test_write_project_version_missing_project(tmp_path: Path) -> None:
    """Raise ``KeyError`` when the ``[project]`` table is absent."""

    py = tmp_path / "pyproject.toml"
    py.write_text(toml_dumps({}))
    with pytest.raises(KeyError):
        write_project_version("0.1.0", py)
