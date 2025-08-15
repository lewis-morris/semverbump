"""Analyzer plugin registry."""

from __future__ import annotations

from typing import Dict, List, Protocol, Type

from ..compare import Impact
from ..config import Config


class Analyzer(Protocol):
    """Protocol for analyzer plugins.

    An analyzer collects state for a given git reference and compares two
    states to produce :class:`Impact` entries.
    """

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyzer with configuration."""

    def collect(self, ref: str) -> object:
        """Collect analyzer-specific state at ``ref``."""

    def compare(self, old: object, new: object) -> List[Impact]:
        """Compare two states and return impacts."""


REGISTRY: Dict[str, Type[Analyzer]] = {}


def register(name: str):
    """Decorator registering an analyzer implementation."""

    def _wrap(cls: Type[Analyzer]) -> Type[Analyzer]:
        REGISTRY[name] = cls
        return cls

    return _wrap


def load_enabled(cfg: Config) -> List[Analyzer]:
    """Instantiate analyzers enabled via configuration."""
    out: List[Analyzer] = []
    for name in cfg.analyzers.enabled:
        cls = REGISTRY.get(name)
        if cls:
            out.append(cls(cfg))
    return out


def available() -> List[str]:
    """Return names of all registered analyzers."""
    return sorted(REGISTRY.keys())


# Import built-in analyzers for registration side-effects
from . import cli, web_routes  # noqa: F401,E402
