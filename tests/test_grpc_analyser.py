"""Tests for the gRPC analyser."""

from bumpwright.analysers.grpc import (
    Service,
    diff_services,
    extract_services_from_proto,
)


def _build(src: str) -> dict[str, Service]:
    """Parse proto source into a service mapping."""
    return extract_services_from_proto(src)


def test_removed_service_is_major() -> None:
    """Removing a service triggers a major impact."""
    old = _build(
        """
        service Foo {
            rpc Ping (Req) returns (Res);
        }
        """
    )
    new: dict[str, Service] = {}
    impacts = diff_services(old, new)
    assert any(i.severity == "major" for i in impacts)


def test_added_service_is_minor() -> None:
    """Adding a service triggers a minor impact."""
    old: dict[str, Service] = {}
    new = _build(
        """
        service Foo {
            rpc Ping (Req) returns (Res);
        }
        """
    )
    impacts = diff_services(old, new)
    assert any(i.severity == "minor" for i in impacts)


def test_removed_method_is_major() -> None:
    """Removing a method from a service is a major impact."""
    old = _build(
        """
        service Foo {
            rpc Ping (Req) returns (Res);
            rpc Pong (Req) returns (Res);
        }
        """
    )
    new = _build(
        """
        service Foo {
            rpc Ping (Req) returns (Res);
        }
        """
    )
    impacts = diff_services(old, new)
    assert any(i.severity == "major" and i.symbol == "Foo.Pong" for i in impacts)


def test_added_method_is_minor() -> None:
    """Adding a method to a service is a minor impact."""
    old = _build(
        """
        service Foo {
            rpc Ping (Req) returns (Res);
        }
        """
    )
    new = _build(
        """
        service Foo {
            rpc Ping (Req) returns (Res);
            rpc Pong (Req) returns (Res);
        }
        """
    )
    impacts = diff_services(old, new)
    assert any(i.severity == "minor" and i.symbol == "Foo.Pong" for i in impacts)
