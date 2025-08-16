"""Integration tests for opt-in analyser behaviour."""

from pathlib import Path

from bumpwright.analysers import load_enabled
from bumpwright.config import load_config


def test_no_analyser_enabled_by_default(tmp_path: Path) -> None:
    """Verify that analysers are inactive without explicit configuration.

    Args:
        tmp_path: Temporary directory for an isolated config path.
    """
    cfg = load_config(tmp_path / "bumpwright.toml")
    analysers = load_enabled(cfg)
    assert analysers == []
