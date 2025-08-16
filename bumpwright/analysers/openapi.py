"""OpenAPI specification analyser.

Parses OpenAPI YAML or JSON documents to detect endpoint and schema changes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..compare import Impact
from ..config import Config
from ..gitutils import read_files_at_ref
from . import register

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Operation:
    """Details of a single API operation."""

    parameters: dict[tuple[str, str], bool]
    responses: dict[str, Any]


@dataclass(frozen=True)
class Spec:
    """Collected data from an OpenAPI specification.

    Attributes:
        endpoints: Set of ``(path, method)`` tuples for all operations.
        schemas: Mapping of component schema names to their definitions.
        operations: Mapping of endpoints to operation details.
    """

    endpoints: set[tuple[str, str]]
    schemas: dict[str, Any]
    operations: dict[tuple[str, str], Operation]


def _parse_spec(content: str) -> Spec:
    """Parse an OpenAPI document string.

    Invalid documents are ignored with a warning, returning an empty
    :class:`Spec`.

    Args:
        content: YAML or JSON formatted OpenAPI document.

    Returns:
        Parsed :class:`Spec` containing endpoints, parameters, responses, and
        schema definitions, or an empty :class:`Spec` if parsing fails.
    """

    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        logger.warning("Failed to parse OpenAPI spec: %s", exc)
        return Spec(endpoints=set(), schemas={}, operations={})
    paths: dict[str, dict[str, Any]] = data.get("paths", {})
    endpoints: set[tuple[str, str]] = set()
    operations: dict[tuple[str, str], Operation] = {}
    for path, path_item in paths.items():
        path_params = {
            (p.get("name", ""), p.get("in", "")): p.get("required", False)
            for p in path_item.get("parameters", [])
        }
        for method, op in path_item.items():
            if method == "parameters":
                continue
            meth = method.upper()
            endpoints.add((path, meth))
            op_params = path_params.copy()
            for param in op.get("parameters", []):
                key = (param.get("name", ""), param.get("in", ""))
                op_params[key] = param.get("required", False)
            responses = {}
            for status, resp in op.get("responses", {}).items():
                schema = (
                    resp.get("content", {}).get("application/json", {}).get("schema")
                )
                if schema is not None:
                    responses[status] = schema
            operations[(path, meth)] = Operation(
                parameters=op_params, responses=responses
            )
    schemas = data.get("components", {}).get("schemas", {})
    return Spec(endpoints=endpoints, schemas=schemas, operations=operations)


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

    for ep in old.operations.keys() & new.operations.keys():
        old_op = old.operations[ep]
        new_op = new.operations[ep]

        for param in old_op.parameters.keys() - new_op.parameters.keys():
            impacts.append(
                Impact("major", f"{ep[1]} {ep[0]}", f"Removed parameter {param[0]}")
            )
        for param in new_op.parameters.keys() - old_op.parameters.keys():
            impacts.append(
                Impact("minor", f"{ep[1]} {ep[0]}", f"Added parameter {param[0]}")
            )
        for param in old_op.parameters.keys() & new_op.parameters.keys():
            old_req = old_op.parameters[param]
            new_req = new_op.parameters[param]
            if old_req != new_req:
                severity = "major" if new_req and not old_req else "minor"
                change = "now required" if new_req else "no longer required"
                impacts.append(
                    Impact(
                        severity,
                        f"{ep[1]} {ep[0]}",
                        f"Parameter {param[0]} {change}",
                    )
                )

        for status in old_op.responses.keys() - new_op.responses.keys():
            impacts.append(
                Impact("major", f"{ep[1]} {ep[0]}", f"Removed response {status}")
            )
        for status in new_op.responses.keys() - old_op.responses.keys():
            impacts.append(
                Impact("minor", f"{ep[1]} {ep[0]}", f"Added response {status}")
            )
        for status in old_op.responses.keys() & new_op.responses.keys():
            if old_op.responses[status] != new_op.responses[status]:
                impacts.append(
                    Impact(
                        "major",
                        f"{ep[1]} {ep[0]}",
                        f"Changed response {status} schema",
                    )
                )

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
        operations: dict[tuple[str, str], Operation] = {}
        for content in contents.values():
            if content is None:
                continue
            spec = _parse_spec(content)
            endpoints |= spec.endpoints
            schemas.update(spec.schemas)
            operations.update(spec.operations)
        return Spec(endpoints=endpoints, schemas=schemas, operations=operations)

    def compare(self, old: Spec, new: Spec) -> list[Impact]:
        """Compare two collected specs and report impacts."""

        return diff_specs(old, new)
