"""Detect gRPC service and method changes across git references."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from fnmatch import fnmatch
from functools import lru_cache
from pathlib import Path

from ..compare import Impact
from ..config import Config
from ..gitutils import _run, read_files_at_ref
from . import register

SERVICE_RE = re.compile(r"\bservice\s+(\w+)\s*\{")
RPC_RE = re.compile(r"\brpc\s+(\w+)\s*\(")


@dataclass(frozen=True)
class Service:
    """Representation of a gRPC service."""

    name: str
    methods: set[str]


def _strip_comments(code: str) -> str:
    """Remove line and block comments from proto source."""
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    out_lines = []
    for line in code.splitlines():
        out_lines.append(line.split("//", 1)[0])
    return "\n".join(out_lines)


def extract_services_from_proto(code: str) -> dict[str, Service]:
    """Parse `.proto` text into gRPC services.

    Args:
        code: Protocol buffer definition text.

    Returns:
        Mapping of service name to :class:`Service` objects.
    """
    text = _strip_comments(code)
    services: dict[str, Service] = {}
    current: Service | None = None
    brace_depth = 0
    for line in text.splitlines():
        if current is None:
            m = SERVICE_RE.search(line)
            if m:
                name = m.group(1)
                current = Service(name, set())
                services[name] = current
                brace_depth = line.count("{") - line.count("}")
            continue
        brace_depth += line.count("{") - line.count("}")
        m = RPC_RE.search(line)
        if m:
            current.methods.add(m.group(1))
        if brace_depth <= 0:
            current = None
    return services


@lru_cache(maxsize=None)
def _list_proto_files_at_ref_cached(
    ref: str,
    roots: tuple[str, ...],
    ignore_globs: tuple[str, ...],
    cwd: str | None,
) -> frozenset[str]:
    """Return cached proto file paths for a git ref."""
    out = _run(["git", "ls-tree", "-r", "--name-only", ref], cwd)
    paths: set[str] = set()
    roots_norm = [str(Path(r)) for r in roots]
    for line in out.splitlines():
        if not line.endswith(".proto"):
            continue
        p = Path(line)
        if any(str(p).startswith(r.rstrip("/") + "/") or str(p) == r for r in roots_norm):
            s = str(p)
            if ignore_globs and any(fnmatch(s, pat) for pat in ignore_globs):
                continue
            paths.add(s)
    return frozenset(paths)


def list_proto_files_at_ref(
    ref: str,
    roots: Iterable[str],
    ignore_globs: Iterable[str] | None = None,
    cwd: str | None = None,
) -> set[str]:
    """List `.proto` files under ``roots`` at ``ref``."""
    roots_tuple = tuple(roots)
    ignores_tuple = tuple(ignore_globs or ())
    return set(_list_proto_files_at_ref_cached(ref, roots_tuple, ignores_tuple, cwd))


list_proto_files_at_ref.cache_clear = _list_proto_files_at_ref_cached.cache_clear  # type: ignore[attr-defined]


def _build_services_at_ref(ref: str, roots: Iterable[str], ignores: Iterable[str]) -> dict[str, Service]:
    """Collect gRPC services from `.proto` files at ``ref``.

    Args:
        ref: Git reference to inspect.
        roots: Root directories to search for proto files.
        ignores: Glob patterns to exclude.

    Returns:
        Mapping of service name to :class:`Service` objects discovered.
    """
    paths = list_proto_files_at_ref(ref, roots, ignore_globs=ignores)
    contents = read_files_at_ref(ref, paths)
    services: dict[str, Service] = {}
    for path in paths:
        code = contents.get(path)
        if code is None:
            continue
        services.update(extract_services_from_proto(code))
    return services


def diff_services(old: dict[str, Service], new: dict[str, Service]) -> list[Impact]:
    """Compute impacts between two gRPC service mappings.

    Args:
        old: Mapping of services for the base reference.
        new: Mapping of services for the head reference.

    Returns:
        List of detected impacts between the two mappings.
    """
    impacts: list[Impact] = []
    for svc in old.keys() - new.keys():
        impacts.append(Impact("major", svc, "Removed service"))
    for svc in new.keys() - old.keys():
        impacts.append(Impact("minor", svc, "Added service"))
    for svc in old.keys() & new.keys():
        old_methods = old[svc].methods
        new_methods = new[svc].methods
        for m in old_methods - new_methods:
            impacts.append(Impact("major", f"{svc}.{m}", "Removed RPC method"))
        for m in new_methods - old_methods:
            impacts.append(Impact("minor", f"{svc}.{m}", "Added RPC method"))
    return impacts


@register("grpc", "Track changes in gRPC services and RPC methods.")
class GrpcAnalyser:
    """Analyser plugin for gRPC `.proto` definitions."""

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyser with configuration."""
        self.cfg = cfg

    def collect(self, ref: str) -> dict[str, Service]:
        """Collect gRPC service definitions at ``ref``.

        Args:
            ref: Git reference to inspect.

        Returns:
            Mapping of service name to :class:`Service` objects.
        """
        return _build_services_at_ref(ref, self.cfg.project.public_roots, self.cfg.ignore.paths)

    def compare(self, old: dict[str, Service], new: dict[str, Service]) -> list[Impact]:
        """Compare two gRPC service mappings and return impacts.

        Args:
            old: Baseline service mapping.
            new: Updated service mapping.

        Returns:
            List of impacts describing gRPC changes.
        """
        return diff_services(old, new)
