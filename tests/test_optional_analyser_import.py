"""Tests for optional analyser imports."""

from __future__ import annotations

import importlib
import sys


def test_missing_optional_dependencies_do_not_error(monkeypatch) -> None:
    """Ensure analyzers with missing dependencies are skipped."""
    monkeypatch.setitem(sys.modules, "graphql", None)
    mod = importlib.reload(importlib.import_module("bumpwright.analysers"))
    assert "graphql" not in mod.REGISTRY
