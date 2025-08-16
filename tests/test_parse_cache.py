from __future__ import annotations

import ast
import os
from pathlib import Path
from unittest.mock import patch

from bumpwright import gitutils
from bumpwright.analysers.cli import _build_cli_at_ref
from bumpwright.analysers.utils import clear_caches, parse_python_source


def _init_repo(tmp_path: Path) -> Path:
    """Create a git repository with a simple CLI module."""
    repo = tmp_path / "repo"
    repo.mkdir()
    pkg = repo / "pkg"
    pkg.mkdir()
    (pkg / "cli.py").write_text(
        """
import click

@click.command()
def main() -> None:
    pass
"""
    )
    gitutils._run(["git", "init"], str(repo))
    gitutils._run(["git", "config", "user.email", "test@example.com"], str(repo))
    gitutils._run(["git", "config", "user.name", "Test"], str(repo))
    gitutils._run(["git", "add", "."], str(repo))
    gitutils._run(["git", "commit", "-m", "init"], str(repo))
    return repo


def test_parse_python_source_caches(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    clear_caches()
    path = "pkg/cli.py"
    with (
        patch(
            "bumpwright.analysers.utils.read_file_at_ref",
            wraps=gitutils.read_file_at_ref,
        ) as rf,
        patch("bumpwright.analysers.utils.ast.parse", wraps=ast.parse) as ap,
    ):
        tree1 = parse_python_source("HEAD", path, str(repo))
        tree2 = parse_python_source("HEAD", path, str(repo))
        assert tree1 is tree2
        assert rf.call_count == 1  # noqa: PLR2004
        assert ap.call_count == 1  # noqa: PLR2004
        clear_caches()
        parse_python_source("HEAD", path, str(repo))
        assert rf.call_count == 2  # noqa: PLR2004
        assert ap.call_count == 2  # noqa: PLR2004


def test_build_cli_uses_cached_ast(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    clear_caches()
    with patch("bumpwright.analysers.utils.ast.parse", wraps=ast.parse) as ap:
        old = os.getcwd()
        os.chdir(repo)
        try:
            _build_cli_at_ref("HEAD", ["pkg"], [])
            _build_cli_at_ref("HEAD", ["pkg"], [])
        finally:
            os.chdir(old)
        assert ap.call_count == 1  # noqa: PLR2004
