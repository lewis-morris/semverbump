"""Analyzer plugin registry and utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Protocol, Type

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

    def compare(self, old: object, new: object) -> List[Impact]:
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
    cls: Type[Analyzer]
    description: str


REGISTRY: Dict[str, AnalyzerInfo] = {}


def register(
    name: str, description: str | None = None
) -> Callable[[Type[Analyzer]], Type[Analyzer]]:
    """Decorator registering an analyzer implementation.

    Args:
        name: Registry key used to enable the analyzer via configuration.
        description: Optional human-readable description. Defaults to the
            analyzer class's docstring.

    Returns:
        Decorator that registers the analyzer class.
    """

    def _wrap(cls: Type[Analyzer]) -> Type[Analyzer]:
        desc = description or (cls.__doc__ or "").strip()
        REGISTRY[name] = AnalyzerInfo(name=name, cls=cls, description=desc)
        return cls

    return _wrap


def load_enabled(cfg: Config, names: Iterable[str] | None = None) -> List[Analyzer]:
    """Instantiate analyzers enabled via configuration or overrides.

    Args:
        cfg: Global configuration object.
        names: Optional explicit collection of analyzer names to load. When
            ``None``, the names configured in ``cfg`` are used.

    Returns:
        List of instantiated analyzers.

    Raises:
        ValueError: If a requested analyzer name is not registered.
    """

    selected = set(cfg.analyzers.enabled if names is None else names)
    out: List[Analyzer] = []
    for name in selected:
        info = REGISTRY.get(name)
        if info is None:
            raise ValueError(f"Analyzer '{name}' is not registered")
        out.append(info.cls(cfg))
    return out


def available() -> List[str]:
    """Return names of all registered analyzers."""
    return sorted(REGISTRY.keys())


def get_analyzer_info(name: str) -> AnalyzerInfo | None:
    """Return registry information for ``name`` if available."""
    return REGISTRY.get(name)


# Import built-in analyzers for registration side-effects
# isort: off
# fmt: off
from . import cli, web_routes  # noqa: F401,E402  # pylint: disable=wrong-import-position
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
