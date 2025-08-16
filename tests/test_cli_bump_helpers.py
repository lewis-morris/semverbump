import argparse
import json
import logging
import os
from pathlib import Path

import pytest
from cli_helpers import run, setup_repo

from bumpwright.compare import Decision
from bumpwright.config import load_config
from bumpwright.versioning import VersionChange

from bumpwright.cli.bump import (  # isort:skip
    _commit_tag,
    _display_result,
    _prepare_version_files,
    _resolve_pyproject,
    _read_template,
    _build_changelog,
    get_default_template,
    _write_changelog,
)


def test_prepare_version_files_no_relevant_changes(tmp_path: Path) -> None:
    repo, _, base = setup_repo(tmp_path)
    pyproj = repo / "pyproject.toml"
    pyproj.write_text(pyproj.read_text().replace("0.1.0", "0.1.1"), encoding="utf-8")
    run(["git", "add", "pyproject.toml"], repo)
    run(["git", "commit", "-m", "chore: bump version"], repo)
    cfg = load_config(repo / "bumpwright.toml")
    args = argparse.Namespace(version_path=["pkg*/__init__.py"])
    cwd = os.getcwd()
    os.chdir(repo)
    try:
        paths = _prepare_version_files(cfg, args, pyproj, base, "HEAD")
    finally:
        os.chdir(cwd)
    assert paths is None


def test_prepare_version_files_wildcard_directory(tmp_path: Path) -> None:
    repo, _, base = setup_repo(tmp_path)
    extra_pkg = repo / "pkg_extra"
    extra_pkg.mkdir()
    init_file = extra_pkg / "__init__.py"
    init_file.write_text("value = 1\n", encoding="utf-8")
    run(["git", "add", "pkg_extra/__init__.py"], repo)
    run(["git", "commit", "-m", "feat: add extra package"], repo)
    cfg = load_config(repo / "bumpwright.toml")
    args = argparse.Namespace(version_path=["pkg*/__init__.py"])
    pyproj = repo / "pyproject.toml"
    cwd = os.getcwd()
    os.chdir(repo)
    try:
        paths = _prepare_version_files(cfg, args, pyproj, base, "HEAD")
    finally:
        os.chdir(cwd)
    assert paths is not None
    assert "pkg*/__init__.py" in paths


def test_resolve_pyproject_missing() -> None:
    """Ensure resolving a missing pyproject raises an informative error."""

    with pytest.raises(FileNotFoundError, match="pyproject.toml not found at missing.pyproject"):
        _resolve_pyproject("missing.pyproject")


def test_display_result_json(caplog) -> None:
    args = argparse.Namespace(format="json")
    vc = VersionChange("0.1.0", "0.2.0", "minor", [Path("pyproject.toml")])
    dec = Decision("minor", 1.0, [])
    with caplog.at_level(logging.INFO):
        _display_result(args, vc, dec)
    data = json.loads(caplog.records[0].message)
    assert data["new_version"] == "0.2.0"
    assert data["skipped"] == []


def test_display_result_text_skipped(caplog) -> None:
    args = argparse.Namespace(format="text")
    vc = VersionChange(
        "0.1.0",
        "0.2.0",
        "minor",
        [Path("pyproject.toml")],
        [Path("extra.py")],
    )
    dec = Decision("minor", 1.0, [])
    with caplog.at_level(logging.INFO):
        _display_result(args, vc, dec)
    out = "\n".join(record.message for record in caplog.records)
    assert "Skipped files: extra.py" in out


def test_write_changelog_to_file(tmp_path: Path) -> None:
    args = argparse.Namespace(changelog=str(tmp_path / "CHANGELOG.md"))
    content = "entry\n"
    _write_changelog(args, content)
    assert (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8") == content


def test_read_template_custom(tmp_path: Path) -> None:
    tpl = tmp_path / "tpl.j2"
    tpl.write_text("Hello", encoding="utf-8")
    assert _read_template(str(tpl)) == "Hello"


def test_read_template_default(monkeypatch) -> None:
    def fake_default() -> str:
        return "Hi"

    monkeypatch.setattr("bumpwright.cli.bump.get_default_template", fake_default)
    assert _read_template(None) == "Hi"


def test_get_default_template_reads_file() -> None:
    expected = (Path(__file__).resolve().parents[1] / "bumpwright" / "templates" / "changelog.md.j2").read_text(
        encoding="utf-8"
    )
    assert get_default_template() == expected


def test_build_changelog_uses_read_template(monkeypatch) -> None:
    args = argparse.Namespace(changelog="CHANGELOG.md", head="HEAD", repo_url=None, changelog_template=None)
    monkeypatch.setattr("bumpwright.cli.bump.collect_commits", lambda base, head: [])
    monkeypatch.setattr("bumpwright.cli.bump.last_release_commit", lambda: None)
    called = False

    def fake_read(path: str | None) -> str:
        nonlocal called
        called = True
        assert path is None
        return "Version={{ version }}"

    monkeypatch.setattr("bumpwright.cli.bump._read_template", fake_read)
    result = _build_changelog(args, "0.2.0")
    assert called is True
    assert result == "Version=0.2.0\n"


def test_build_changelog_excludes_patterns(monkeypatch) -> None:
    args = argparse.Namespace(
        changelog="CHANGELOG.md",
        head="HEAD",
        repo_url=None,
        changelog_template=None,
        changelog_exclude=["^chore"],
    )
    commits = [("1", "feat: add"), ("2", "chore: skip")]
    monkeypatch.setattr("bumpwright.cli.bump.collect_commits", lambda base, head: commits)
    monkeypatch.setattr("bumpwright.cli.bump.last_release_commit", lambda: None)
    result = _build_changelog(args, "0.2.0")
    assert "feat: add" in result
    assert "chore: skip" not in result


def test_commit_tag_existing_tag(tmp_path: Path) -> None:
    repo, _, _ = setup_repo(tmp_path)
    pyproj = repo / "pyproject.toml"
    # Simulate bumping to a new version that already has a tag
    pyproj.write_text(pyproj.read_text().replace("0.1.0", "0.1.1"), encoding="utf-8")
    run(["git", "tag", "v0.1.1"], repo)
    cwd = os.getcwd()
    os.chdir(repo)
    try:
        with pytest.raises(RuntimeError, match="Tag v0.1.1 already exists"):
            _commit_tag(["pyproject.toml"], "0.1.1", commit=True, tag=True)
    finally:
        os.chdir(cwd)
    head = run(["git", "log", "-1", "--pretty=%s"], repo)
    assert head == "base"


def test_commit_tag_stages_all_files(tmp_path: Path) -> None:
    repo, pkg, _ = setup_repo(tmp_path)
    pyproj = repo / "pyproject.toml"
    init_file = pkg / "__init__.py"
    pyproj.write_text(pyproj.read_text().replace("0.1.0", "0.1.1"), encoding="utf-8")
    init_file.write_text(init_file.read_text() + "\n# change", encoding="utf-8")
    cwd = os.getcwd()
    os.chdir(repo)
    try:
        _commit_tag([pyproj, init_file], "0.1.1", commit=True, tag=False)
    finally:
        os.chdir(cwd)
    files = run(["git", "show", "--pretty=format:", "--name-only", "HEAD"], repo).splitlines()
    assert "pyproject.toml" in files
    assert "pkg/__init__.py" in files
    msg = run(["git", "log", "-1", "--pretty=%s"], repo)
    assert msg == "chore(release): 0.1.1"
