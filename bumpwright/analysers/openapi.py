"""OpenAPI specification analyser.

Parses OpenAPI YAML or JSON documents to detect endpoint and schema changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..compare import Impact
from ..config import Config
from ..gitutils import read_files_at_ref
from . import register


@dataclass(frozen=True)
class Spec:
    """Collected data from an OpenAPI specification.

    Attributes:
        endpoints: Set of ``(path, method)`` tuples for all operations.
        schemas: Mapping of component schema names to their definitions.
    """

    endpoints: set[tuple[str, str]]
    schemas: dict[str, Any]


def _parse_spec(content: str) -> Spec:
    """Parse an OpenAPI document string.

    Args:
        content: YAML or JSON formatted OpenAPI document.

    Returns:
        Parsed :class:`Spec` containing endpoints and schema definitions.
    """

    data = yaml.safe_load(content) or {}
    paths: dict[str, dict[str, Any]] = data.get("paths", {})
    endpoints: set[tuple[str, str]] = set()
    for path, methods in paths.items():
        for method in methods:
            endpoints.add((path, method.upper()))
    schemas = data.get("components", {}).get("schemas", {})
    return Spec(endpoints=endpoints, schemas=schemas)


def diff_specs(old: Spec, new: Spec) -> list[Impact]:
    """Compare two specs and return API impacts.

    Args:
        old: Specification from the base reference.
        new: Specification from the head reference.

    Returns:
        List of :class:`Impact` entries describing differences.
    """

    impacts: list[Impact] = []
    for ep in old.endpoints - new.endpoints:
        impacts.append(Impact("major", f"{ep[1]} {ep[0]}", "Removed endpoint"))
    for ep in new.endpoints - old.endpoints:
        impacts.append(Impact("minor", f"{ep[1]} {ep[0]}", "Added endpoint"))
    for name in old.schemas.keys() - new.schemas.keys():
        impacts.append(Impact("major", name, "Removed schema"))
    for name in new.schemas.keys() - old.schemas.keys():
        impacts.append(Impact("minor", name, "Added schema"))
    for name in old.schemas.keys() & new.schemas.keys():
        if old.schemas[name] != new.schemas[name]:
            impacts.append(Impact("major", name, "Changed schema"))
    return impacts


@register("openapi", "Analyze OpenAPI specs for API changes.")
class OpenAPIAnalyser:
    """Analyser plugin for OpenAPI specification files."""

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyser with configuration.

        Args:
            cfg: Global configuration object.
        """

        self.cfg = cfg

    def collect(self, ref: str) -> Spec:
        """Collect OpenAPI spec data at ``ref``.

        Args:
            ref: Git reference to read from.

        Returns:
            Combined specification data from all configured paths.
        """

        paths = [str(Path(p)) for p in self.cfg.openapi.paths]
        contents = read_files_at_ref(ref, paths)
        endpoints: set[tuple[str, str]] = set()
        schemas: dict[str, Any] = {}
        for content in contents.values():
            if content is None:
                continue
            spec = _parse_spec(content)
            endpoints |= spec.endpoints
            schemas.update(spec.schemas)
        return Spec(endpoints=endpoints, schemas=schemas)

    def compare(self, old: Spec, new: Spec) -> list[Impact]:
        """Compare two collected specs and report impacts."""

        return diff_specs(old, new)
