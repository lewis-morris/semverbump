"""Analyzer plugin registry and utilities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from ..compare import Impact
from ..config import Config


class Analyzer(Protocol):
    """Protocol for analyzer plugins.

    Analyzer implementations capture domain-specific state for a git
    reference and compare two such states to generate :class:`Impact`
    entries describing any public API changes.
    """

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyzer with configuration."""

    def collect(self, ref: str) -> object:
        """Collect analyzer-specific state at ``ref``."""

    def compare(self, old: object, new: object) -> list[Impact]:
        """Compare two states and return impacts."""


@dataclass(frozen=True)
class AnalyzerInfo:
    """Metadata describing a registered analyzer.

    Attributes:
        name: Unique identifier for the analyzer.
        cls: Implementation class used to instantiate the analyzer.
        description: Human-readable description of the analyzer.
    """

    name: str
    cls: type[Analyzer]
    description: str


REGISTRY: dict[str, AnalyzerInfo] = {}


def register(
    name: str, description: str | None = None
) -> Callable[[type[Analyzer]], type[Analyzer]]:
    """Decorator registering an analyzer implementation.

    Args:
        name: Registry key used to enable the analyzer via configuration.
        description: Optional human-readable description. Defaults to the
            analyzer class's docstring.

    Returns:
        Decorator that registers the analyzer class.
    """

    def _wrap(cls: type[Analyzer]) -> type[Analyzer]:
        desc = description or (cls.__doc__ or "").strip()
        REGISTRY[name] = AnalyzerInfo(name=name, cls=cls, description=desc)
        return cls

    return _wrap


def load_enabled(cfg: Config) -> list[Analyzer]:
    """Instantiate analyzers enabled via configuration.

    Args:
        cfg: Global configuration object.

    Returns:
        List of instantiated analyzers.

    Raises:
        ValueError: If a configured analyzer name is not registered.
    """

    out: list[Analyzer] = []
    for name in cfg.analyzers.enabled:
        info = REGISTRY.get(name)
        if info is None:
            raise ValueError(f"Analyzer '{name}' is not registered")
        out.append(info.cls(cfg))
    return out


def available() -> list[str]:
    """Return names of all registered analyzers."""
    return sorted(REGISTRY.keys())


def get_analyzer_info(name: str) -> AnalyzerInfo | None:
    """Return registry information for ``name`` if available."""
    return REGISTRY.get(name)


# Import built-in analyzers for registration side-effects
# isort: off
# fmt: off
from . import cli, migrations, web_routes  # noqa: F401,E402  # pylint: disable=wrong-import-position
# fmt: on
# isort: on

__all__ = [
    "Analyzer",
    "AnalyzerInfo",
    "register",
    "load_enabled",
    "available",
    "get_analyzer_info",
]
