"""Analyzer plugin registry and utilities."""

from __future__ import annotations

from typing import Callable, Dict, List, Protocol, Type

from ..compare import Impact
from ..config import Config


class Analyzer(Protocol):
    """Protocol for analyzer plugins.

    An analyzer collects state for a given Git reference and compares two
    states to produce :class:`Impact` entries.
    """

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyzer.

        Args:
            cfg: Project configuration.
        """

    def collect(self, ref: str) -> object:
        """Collect analyzer-specific state.

        Args:
            ref: Git reference to inspect.

        Returns:
            An object representing the analyzer state at ``ref``.
        """

    def compare(self, old: object, new: object) -> List[Impact]:
        """Compare two states and return impacts.

        Args:
            old: State from the base reference.
            new: State from the head reference.

        Returns:
            A list of impacts describing differences between states.
        """


REGISTRY: Dict[str, Type[Analyzer]] = {}


class AnalyzerRegistryError(RuntimeError):
    """Base exception for analyzer registry errors."""


class AnalyzerRegistrationError(AnalyzerRegistryError):
    """Raised when attempting to register a duplicate analyzer."""


class AnalyzerNotFoundError(AnalyzerRegistryError):
    """Raised when a requested analyzer is not registered."""


def register(
    name: str, *, override: bool = False
) -> Callable[[Type[Analyzer]], Type[Analyzer]]:
    """Decorator registering an analyzer implementation.

    Args:
        name: Unique identifier for the analyzer.
        override: Replace an existing registration if ``True``.

    Raises:
        AnalyzerRegistrationError: If ``name`` is already registered and
            ``override`` is ``False``.

    Returns:
        The original class.
    """

    def _wrap(cls: Type[Analyzer]) -> Type[Analyzer]:
        if not override and name in REGISTRY:
            raise AnalyzerRegistrationError(f"Analyzer '{name}' already registered")
        REGISTRY[name] = cls
        return cls

    return _wrap


def get(name: str) -> Type[Analyzer]:
    """Return the analyzer class registered under ``name``.

    Args:
        name: Registered analyzer name.

    Raises:
        AnalyzerNotFoundError: If no analyzer has been registered under ``name``.

    Returns:
        The analyzer class associated with ``name``.
    """

    try:
        return REGISTRY[name]
    except KeyError as exc:  # pragma: no cover - defensive programming
        raise AnalyzerNotFoundError(f"Analyzer '{name}' not found") from exc


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
# isort: off
# fmt: off
from . import cli, web_routes  # noqa: F401,E402  # pylint: disable=wrong-import-position
# fmt: on
# isort: on

__all__ = [
    "Analyzer",
    "register",
    "get",
    "load_enabled",
    "available",
    "AnalyzerRegistryError",
    "AnalyzerRegistrationError",
    "AnalyzerNotFoundError",
]
