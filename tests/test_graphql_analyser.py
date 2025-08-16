from __future__ import annotations

from bumpwright.analysers.graphql_schema import (
    TypeDef,
    diff_types,
    extract_types_from_schema,
)


def _build(sdl: str) -> dict[str, TypeDef]:
    """Parse SDL into type definitions."""

    return extract_types_from_schema(sdl)


def test_removed_type_is_major() -> None:
    """Removing a type should trigger a major impact."""

    old = _build("type User { id: ID! }")
    new: dict[str, TypeDef] = {}
    impacts = diff_types(old, new)
    assert any(i.severity == "major" and i.symbol == "User" for i in impacts)


def test_added_type_is_minor() -> None:
    """Adding a type should trigger a minor impact."""

    old: dict[str, TypeDef] = {}
    new = _build("type User { id: ID! }")
    impacts = diff_types(old, new)
    assert any(i.severity == "minor" and i.symbol == "User" for i in impacts)


def test_added_field_is_minor() -> None:
    """Adding a field is a minor change."""

    old = _build("type User { id: ID! }")
    new = _build("type User { id: ID!, name: String }")
    impacts = diff_types(old, new)
    assert any(i.severity == "minor" and i.symbol == "User.name" for i in impacts)


def test_removed_field_is_major() -> None:
    """Removing a field is a major change."""

    old = _build("type User { id: ID!, name: String }")
    new = _build("type User { id: ID! }")
    impacts = diff_types(old, new)
    assert any(i.severity == "major" and i.symbol == "User.name" for i in impacts)
