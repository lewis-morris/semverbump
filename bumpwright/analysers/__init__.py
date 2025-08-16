"""Analyser plugin registry and utilities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from ..compare import Impact
from ..config import Config


class Analyser(Protocol):
    """Protocol for analyser plugins.

    Analyser implementations capture domain-specific state for a git
    reference and compare two such states to generate :class:`Impact`
    entries describing any public API changes.
    """

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyser with configuration."""

    def collect(self, ref: str) -> object:
        """Collect analyser-specific state at ``ref``."""

    def compare(self, old: object, new: object) -> list[Impact]:
        """Compare two states and return impacts."""


@dataclass(frozen=True)
class AnalyserInfo:
    """Metadata describing a registered analyser.

    Attributes:
        name: Unique identifier for the analyser.
        cls: Implementation class used to instantiate the analyser.
        description: Human-readable description of the analyser.
    """

    name: str
    cls: type[Analyser]
    description: str


REGISTRY: dict[str, AnalyserInfo] = {}


def register(name: str, description: str | None = None) -> Callable[[type[Analyser]], type[Analyser]]:
    """Decorator registering an analyser implementation.

    Args:
        name: Registry key used to enable the analyser via configuration.
        description: Optional human-readable description. Defaults to the
            analyser class's docstring.

    Returns:
        Decorator that registers the analyser class.
    """

    def _wrap(cls: type[Analyser]) -> type[Analyser]:
        desc = description or (cls.__doc__ or "").strip()
        REGISTRY[name] = AnalyserInfo(name=name, cls=cls, description=desc)
        return cls

    return _wrap


def load_enabled(cfg: Config) -> list[Analyser]:
    """Instantiate analysers enabled via configuration.

    Args:
        cfg: Global configuration object.

    Returns:
        List of instantiated analysers.

    Raises:
        ValueError: If a configured analyser name is not registered.
    """

    out: list[Analyser] = []
    for name in cfg.analysers.enabled:
        info = REGISTRY.get(name)
        if info is None:
            raise ValueError(f"Analyser '{name}' is not registered")
        out.append(info.cls(cfg))
    return out


def available() -> list[str]:
    """Return names of all registered analysers."""
    return sorted(REGISTRY.keys())


def get_analyser_info(name: str) -> AnalyserInfo | None:
    """Return registry information for ``name`` if available."""
    return REGISTRY.get(name)


# Import built-in analysers for registration side-effects
# isort: off
# fmt: off
from . import cli, migrations, grpc, openapi, graphql_schema, web_routes  # noqa: F401,E402  # pylint: disable=wrong-import-position

# fmt: on
# isort: on

__all__ = [
    "Analyser",
    "AnalyserInfo",
    "register",
    "load_enabled",
    "available",
    "get_analyser_info",
]
