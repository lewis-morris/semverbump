"""Integration tests for combining analyzer plugins."""

import os
import subprocess
from pathlib import Path
from typing import List, Set

try:  # pragma: no cover - handled when pytest not installed
    import pytest
except ModuleNotFoundError:  # pragma: no cover
    pytest = None  # type: ignore

from bumpwright.analyzers import load_enabled
from bumpwright.compare import Impact
from bumpwright.config import Config, Project


def _run(cmd: List[str], cwd: Path) -> str:
    """Run ``cmd`` in ``cwd`` and return stdout."""
    res = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return res.stdout.strip()


def _setup_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """Create a repository with both CLI and web route code."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init"], repo)
    _run(["git", "config", "user.email", "a@b.c"], repo)
    _run(["git", "config", "user.name", "tester"], repo)

    pkg = repo / "pkg"
    pkg.mkdir()

    # Base commit with a CLI command and a web route
    (pkg / "cli.py").write_text(
        """
import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
p_run = sub.add_parser('run')
"""
    )
    (pkg / "web.py").write_text(
        """
from flask import Flask
app = Flask(__name__)

@app.route('/foo')
def foo():
    return 'ok'
"""
    )
    _run(["git", "add", "pkg"], repo)
    _run(["git", "commit", "-m", "base"], repo)
    base = _run(["git", "rev-parse", "HEAD"], repo)

    # Head commit removes the CLI command and the web route
    (pkg / "cli.py").write_text(
        """
import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
"""
    )
    (pkg / "web.py").write_text(
        """
from flask import Flask
app = Flask(__name__)
"""
    )
    _run(["git", "add", "pkg"], repo)
    _run(["git", "commit", "-m", "head"], repo)
    head = _run(["git", "rev-parse", "HEAD"], repo)
    return repo, base, head


@pytest.mark.parametrize(
    "enabled,expected",
    [
        ({"cli"}, [Impact("major", "run", "Removed command")]),
        (
            {"cli", "web_routes"},
            [
                Impact("major", "run", "Removed command"),
                Impact("major", "GET /foo", "Removed route"),
            ],
        ),
    ],
)
def test_combined_analyzers(
    tmp_path: Path, enabled: Set[str], expected: List[Impact]
) -> None:
    """Ensure multiple analyzers produce combined impacts."""
    repo, base, head = _setup_repo(tmp_path)

    cfg = Config(project=Project(public_roots=["pkg"]))
    cfg.analyzers.enabled.update(enabled)
    analyzers = load_enabled(cfg)

    impacts: List[Impact] = []
    old_cwd = os.getcwd()
    os.chdir(repo)
    try:
        for analyzer in analyzers:
            old_state = analyzer.collect(base)
            new_state = analyzer.collect(head)
            impacts.extend(analyzer.compare(old_state, new_state))
    finally:
        os.chdir(old_cwd)

    def _key(impact: Impact) -> tuple[str, str]:
        return (impact.symbol, impact.reason)

    assert sorted(impacts, key=_key) == sorted(expected, key=_key)
