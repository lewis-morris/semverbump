"""Analyse GraphQL schema files for breaking changes."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from graphql import parse
from graphql.language import (
    EnumTypeDefinitionNode,
    InputObjectTypeDefinitionNode,
    InterfaceTypeDefinitionNode,
    ObjectTypeDefinitionNode,
    ScalarTypeDefinitionNode,
    UnionTypeDefinitionNode,
)

from ..compare import Impact
from ..config import Config
from ..gitutils import _run, read_files_at_ref
from . import register


@dataclass(frozen=True)
class TypeDef:
    """Represent a GraphQL type and its fields."""

    name: str
    fields: frozenset[str]


def extract_types_from_schema(sdl: str) -> dict[str, TypeDef]:
    """Parse GraphQL SDL into type definitions.

    Args:
        sdl: GraphQL schema definition language string.

    Returns:
        Mapping of type name to :class:`TypeDef` objects.
    """

    doc = parse(sdl)
    out: dict[str, TypeDef] = {}
    for defn in doc.definitions:
        if isinstance(
            defn,
            (
                ObjectTypeDefinitionNode,
                InterfaceTypeDefinitionNode,
                InputObjectTypeDefinitionNode,
            ),
        ):
            fields = frozenset(field.name.value for field in (defn.fields or []))
            out[defn.name.value] = TypeDef(defn.name.value, fields)
        elif isinstance(
            defn,
            (EnumTypeDefinitionNode, UnionTypeDefinitionNode, ScalarTypeDefinitionNode),
        ):
            out[defn.name.value] = TypeDef(defn.name.value, frozenset())
    return out


def diff_types(old: dict[str, TypeDef], new: dict[str, TypeDef]) -> list[Impact]:
    """Compute impacts between two sets of GraphQL types.

    Args:
        old: Type definitions from the base reference.
        new: Type definitions from the head reference.

    Returns:
        List of public API impacts between the two schemas.
    """

    impacts: list[Impact] = []

    for name in old.keys() - new.keys():
        impacts.append(Impact("major", name, "Removed type"))
    for name in new.keys() - old.keys():
        impacts.append(Impact("minor", name, "Added type"))
    for name in old.keys() & new.keys():
        op = old[name].fields
        np = new[name].fields
        for field in op - np:
            impacts.append(Impact("major", f"{name}.{field}", "Removed field"))
        for field in np - op:
            impacts.append(Impact("minor", f"{name}.{field}", "Added field"))
    return impacts


def _list_graphql_files_at_ref(
    ref: str, roots: Iterable[str], ignore_globs: Iterable[str], cwd: str | None = None
) -> set[str]:
    """List ``.graphql`` files under given roots at ``ref``."""

    out = _run(["git", "ls-tree", "-r", "--name-only", ref], cwd)
    paths: set[str] = set()
    roots_norm = [str(Path(r)) for r in roots]
    for line in out.splitlines():
        if not line.endswith(".graphql"):
            continue
        p = Path(line)
        if any(str(p).startswith(r.rstrip("/") + "/") or str(p) == r for r in roots_norm):
            s = str(p)
            if ignore_globs and any(fnmatch(s, pat) for pat in ignore_globs):
                continue
            paths.add(s)
    return paths


def _build_schema_at_ref(ref: str, roots: Iterable[str], ignores: Iterable[str], cwd: str | None = None) -> dict[str, TypeDef]:
    """Collect type definitions from ``.graphql`` files at a git ref."""

    paths = _list_graphql_files_at_ref(ref, roots, ignores, cwd)
    contents = read_files_at_ref(ref, paths, cwd)
    out: dict[str, TypeDef] = {}
    for content in contents.values():
        if content is None:
            continue
        out.update(extract_types_from_schema(content))
    return out


@register("graphql", "Analyze GraphQL schema changes.")
class GraphQLAnalyser:
    """Analyser plugin for GraphQL schemas."""

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyser with configuration."""

        self.cfg = cfg

    def collect(self, ref: str) -> dict[str, TypeDef]:
        """Collect GraphQL types at the given ref."""

        return _build_schema_at_ref(ref, self.cfg.project.public_roots, self.cfg.ignore.paths)

    def compare(self, old: dict[str, TypeDef], new: dict[str, TypeDef]) -> list[Impact]:
        """Compare two schema states and return impacts."""

        return diff_types(old, new)
