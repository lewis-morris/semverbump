"""Version scheme implementations for bumpwright."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from .types import BumpLevel

try:  # pragma: no cover - dependency provided in tests
    from packaging.version import Version
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError("packaging is required for version operations") from exc


MIN_RELEASE_PARTS = 3


# SemVer segments disallow leading zeros per specification.
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-.]+))?(?:\+([0-9A-Za-z-.]+))?$"
)


def _bump_segment(segment: str | None, default: str) -> str:
    """Increment the last numeric component of ``segment``.

    Args:
        segment: Existing dot-separated identifier string.
        default: Prefix used when ``segment`` is ``None``.

    Returns:
        Updated identifier string with the last numeric part incremented. When
        no numeric part is present, ``.1`` is appended.
    """

    if not segment:
        return f"{default}.1"
    parts = segment.split(".")
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].isdigit():
            parts[i] = str(int(parts[i]) + 1)
            return ".".join(parts)
    parts.append("1")
    return ".".join(parts)


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
            version: Version string in ``MAJOR.MINOR.PATCH`` form with optional
                prerelease or build metadata.
            level: Bump level to apply.

        Returns:
            The bumped semantic version string. ``major``, ``minor``, and
            ``patch`` bumps reset any prerelease or build information.

        Raises:
            ValueError: If ``level`` is unknown or ``version`` is invalid.
        """

        match = _SEMVER_RE.match(version)
        if not match:
            raise ValueError(f"Invalid semantic version: {version}")
        major, minor, patch, pre, build = match.groups()
        parts = [int(major), int(minor), int(patch)]
        if level == "major":
            parts = [parts[0] + 1, 0, 0]
            pre = None
            build = None
        elif level == "minor":
            parts = [parts[0], parts[1] + 1, 0]
            pre = None
            build = None
        elif level == "patch":
            parts = [parts[0], parts[1], parts[2] + 1]
            pre = None
            build = None
        elif level == "pre":
            pre = _bump_segment(pre, "rc")
        elif level == "build":
            build = _bump_segment(build, "build")
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unknown level {level}")

        out = f"{parts[0]}.{parts[1]}.{parts[2]}"
        if pre:
            out += f"-{pre}"
        if build:
            out += f"+{build}"
        return out


@dataclass
class Pep440Scheme:
    """Basic PEP 440 bumping preserving the version epoch."""

    def bump(self, version: str, level: BumpLevel) -> str:
        """Bump a PEP 440 compliant version string.

        Args:
            version: Version string to bump.
            level: Bump level to apply.

        Returns:
            The bumped version string with any epoch preserved. ``major``,
            ``minor``, and ``patch`` bumps drop prerelease and local
            components.

        Raises:
            ValueError: If ``level`` is unsupported.
        """

        pv = Version(version)
        epoch = f"{pv.epoch}!" if pv.epoch else ""
        release = list(pv.release)
        pre = pv.pre
        local = pv.local
        while len(release) < MIN_RELEASE_PARTS:
            release.append(0)
        if level == "major":
            release = [release[0] + 1, 0, 0]
            pre = None
            local = None
        elif level == "minor":
            release = [release[0], release[1] + 1, 0]
            pre = None
            local = None
        elif level == "patch":
            release = [release[0], release[1], release[2] + 1]
            pre = None
            local = None
        elif level == "pre":
            if pre:
                pre = (pre[0], pre[1] + 1)
            else:
                pre = ("rc", 1)
        elif level == "build":
            local = _bump_segment(local, "local")
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unknown level {level}")

        release_str = f"{release[0]}.{release[1]}.{release[2]}"
        pre_str = f"{pre[0]}{pre[1]}" if pre else ""
        local_str = f"+{local}" if local else ""
        return f"{epoch}{release_str}{pre_str}{local_str}"


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
