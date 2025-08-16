from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from bumpwright import gitutils
from bumpwright.analysers.utils import clear_caches, parse_python_source
from test_parse_cache import _init_repo


def _init_repo_with_bad_file(tmp_path: Path) -> Path:
    """Create repository containing a syntactically invalid module."""
    repo = _init_repo(tmp_path)
    bad = repo / "pkg" / "bad.py"
    bad.write_text("def broken(\n")
    gitutils._run(["git", "add", "pkg/bad.py"], str(repo))
    gitutils._run(["git", "commit", "-m", "add bad"], str(repo))
    return repo


def test_parse_python_source_skips_invalid(tmp_path: Path) -> None:
    """parse_python_source should return None for invalid Python files."""
    repo = _init_repo_with_bad_file(tmp_path)
    clear_caches()
    assert parse_python_source("HEAD", "pkg/bad.py", str(repo)) is None


def test_parse_python_source_handles_unicode_error(tmp_path: Path) -> None:
    """parse_python_source should return None on UnicodeDecodeError."""
    repo = _init_repo(tmp_path)
    clear_caches()
    path = "pkg/cli.py"
    with patch(
        "bumpwright.analysers.utils.ast.parse",
        side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "error"),
    ):
        assert parse_python_source("HEAD", path, str(repo)) is None
