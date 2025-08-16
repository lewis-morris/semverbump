"""Version scheme implementations for bumpwright."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .types import BumpLevel

try:  # pragma: no cover - dependency provided in tests
    from packaging.version import Version
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError("packaging is required for version operations") from exc


MIN_RELEASE_PARTS = 3


class VersionScheme(Protocol):
    """Protocol for version bumping strategies."""

    def bump(self, version: str, level: BumpLevel) -> str:
        """Return ``version`` bumped by ``level``.

        Args:
            version: Version string to bump.
            level: Bump level to apply.

        Returns:
            The bumped version string.
        """


@dataclass
class SemverScheme:
    """Semantic versioning following the ``MAJOR.MINOR.PATCH`` pattern."""

    def bump(self, version: str, level: BumpLevel) -> str:
        """Bump a semantic version string.

        Args:
            version: Version string in ``X.Y.Z`` form.
            level: Bump level to apply.

        Returns:
            The bumped semantic version.

        Raises:
            ValueError: If ``level`` is unknown.
        """

        pv = Version(version)
        parts = [pv.major, pv.minor, pv.micro]
        if level == "major":
            parts = [parts[0] + 1, 0, 0]
        elif level == "minor":
            parts = [parts[0], parts[1] + 1, 0]
        elif level == "patch":
            parts = [parts[0], parts[1], parts[2] + 1]
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unknown level {level}")
        return f"{parts[0]}.{parts[1]}.{parts[2]}"


@dataclass
class Pep440Scheme:
    """Basic PEP 440 bumping preserving the version epoch."""

    def bump(self, version: str, level: BumpLevel) -> str:
        """Bump a PEP 440 compliant version string.

        Args:
            version: Version string to bump.
            level: Bump level to apply.

        Returns:
            The bumped version string with any epoch preserved.

        Raises:
            ValueError: If ``level`` is unsupported.
        """

        pv = Version(version)
        epoch = f"{pv.epoch}!" if pv.epoch else ""
        release = list(pv.release)
        while len(release) < MIN_RELEASE_PARTS:
            release.append(0)
        if level == "major":
            release = [release[0] + 1, 0, 0]
        elif level == "minor":
            release = [release[0], release[1] + 1, 0]
        elif level == "patch":
            release = [release[0], release[1], release[2] + 1]
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unknown level {level}")
        return f"{epoch}{release[0]}.{release[1]}.{release[2]}"


_SCHEMES: dict[str, VersionScheme] = {
    "semver": SemverScheme(),
    "pep440": Pep440Scheme(),
}


def get_version_scheme(name: str) -> VersionScheme:
    """Return the version scheme instance for ``name``.

    Args:
        name: Identifier of the desired scheme.

    Returns:
        Concrete :class:`VersionScheme` implementation.

    Raises:
        ValueError: If ``name`` is not recognised.
    """

    try:
        return _SCHEMES[name]
    except KeyError as exc:  # pragma: no cover - simple passthrough
        raise ValueError(f"Unknown version scheme: {name}") from exc


__all__ = [
    "VersionScheme",
    "SemverScheme",
    "Pep440Scheme",
    "get_version_scheme",
]
