"""Analyzer plugin registry."""

from __future__ import annotations

from typing import Callable, Dict, List

from ..compare import Impact
from ..config import Config

Analyzer = Callable[[str, str, Config], List[Impact]]

REGISTRY: Dict[str, Analyzer] = {}


def register(name: str, func: Analyzer) -> None:
    """Register an analyzer function."""
    REGISTRY[name] = func


# Import built-in analyzers for registration side-effects
from . import cli, web_routes  # noqa: F401,E402
