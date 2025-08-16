import argparse
import json
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
    _write_changelog,
)


def test_prepare_version_files_no_relevant_changes(tmp_path):
    repo, _, base = setup_repo(tmp_path)
    pyproj = repo / "pyproject.toml"
    pyproj.write_text(pyproj.read_text().replace("0.1.0", "0.1.1"), encoding="utf-8")
    run(["git", "add", "pyproject.toml"], repo)
    run(["git", "commit", "-m", "chore: bump version"], repo)
    cfg = load_config(repo / "bumpwright.toml")
    args = argparse.Namespace(version_path=None)
    cwd = os.getcwd()
    os.chdir(repo)
    try:
        paths = _prepare_version_files(cfg, args, pyproj, base, "HEAD")
    finally:
        os.chdir(cwd)
    assert paths is None


def test_display_result_json(capsys):
    args = argparse.Namespace(format="json")
    vc = VersionChange("0.1.0", "0.2.0", "minor", [Path("pyproject.toml")])
    dec = Decision("minor", 1.0, [])
    _display_result(args, vc, dec)
    data = json.loads(capsys.readouterr().out)
    assert data["new_version"] == "0.2.0"
    assert data["skipped"] == []


def test_display_result_text_skipped(capsys):
    args = argparse.Namespace(format="text")
    vc = VersionChange(
        "0.1.0",
        "0.2.0",
        "minor",
        [Path("pyproject.toml")],
        [Path("extra.py")],
    )
    dec = Decision("minor", 1.0, [])
    _display_result(args, vc, dec)
    out = capsys.readouterr().out
    assert "Skipped files: extra.py" in out


def test_write_changelog_to_file(tmp_path):
    args = argparse.Namespace(changelog=str(tmp_path / "CHANGELOG.md"))
    content = "entry\n"
    _write_changelog(args, content)
    assert (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8") == content


def test_commit_tag_existing_tag(tmp_path):
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


def test_commit_tag_stages_all_files(tmp_path):
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
    files = run(
        ["git", "show", "--pretty=format:", "--name-only", "HEAD"], repo
    ).splitlines()
    assert "pyproject.toml" in files
    assert "pkg/__init__.py" in files
    msg = run(["git", "log", "-1", "--pretty=%s"], repo)
    assert msg == "chore(release): 0.1.1"
