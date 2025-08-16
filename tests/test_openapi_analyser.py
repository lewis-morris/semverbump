from __future__ import annotations

from bumpwright.analysers.openapi import Spec, _parse_spec, diff_specs


def _build(src: str) -> Spec:
    """Parse a spec snippet into a :class:`Spec`."""

    return _parse_spec(src)


def test_removed_endpoint_is_major() -> None:
    """Removing an endpoint triggers a major impact."""

    old = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get: {}
""",
    )
    new = _build(
        """
openapi: 3.0.0
paths: {}
""",
    )
    impacts = diff_specs(old, new)
    assert any(i.severity == "major" for i in impacts)


def test_added_endpoint_is_minor() -> None:
    """Adding a new endpoint triggers a minor impact."""

    old = _build(
        """
openapi: 3.0.0
paths: {}
""",
    )
    new = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    post: {}
""",
    )
    impacts = diff_specs(old, new)
    assert any(i.severity == "minor" for i in impacts)


def test_schema_change_is_major() -> None:
    """Modifying a schema definition is a major impact."""

    old = _build(
        """
openapi: 3.0.0
components:
  schemas:
    Pet:
      type: object
      properties:
        id:
          type: integer
""",
    )
    new = _build(
        """
openapi: 3.0.0
components:
  schemas:
    Pet:
      type: object
      properties:
        id:
          type: string
""",
    )
    impacts = diff_specs(old, new)
    assert any(i.severity == "major" and i.symbol == "Pet" for i in impacts)


def test_parameter_addition_is_minor() -> None:
    """Adding a parameter triggers a minor impact."""

    old = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      parameters:
        - name: id
          in: query
          required: true
""",
    )
    new = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      parameters:
        - name: id
          in: query
          required: true
        - name: type
          in: query
""",
    )
    impacts = diff_specs(old, new)
    assert any(
        i.severity == "minor" and i.reason == "Added parameter type" for i in impacts
    )


def test_parameter_removal_is_major() -> None:
    """Removing a parameter triggers a major impact."""

    old = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      parameters:
        - name: id
          in: query
          required: true
        - name: type
          in: query
""",
    )
    new = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      parameters:
        - name: id
          in: query
          required: true
""",
    )
    impacts = diff_specs(old, new)
    assert any(
        i.severity == "major" and i.reason == "Removed parameter type" for i in impacts
    )


def test_parameter_required_toggle_is_major() -> None:
    """Toggling a parameter to required triggers a major impact."""

    old = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      parameters:
        - name: id
          in: query
""",
    )
    new = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      parameters:
        - name: id
          in: query
          required: true
""",
    )
    impacts = diff_specs(old, new)
    assert any(
        i.severity == "major" and i.reason == "Parameter id now required"
        for i in impacts
    )


def test_parameter_required_toggle_to_optional_is_minor() -> None:
    """Making a parameter optional triggers a minor impact."""

    old = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      parameters:
        - name: id
          in: query
          required: true
""",
    )
    new = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      parameters:
        - name: id
          in: query
""",
    )
    impacts = diff_specs(old, new)
    assert any(
        i.severity == "minor" and i.reason == "Parameter id no longer required"
        for i in impacts
    )


def test_response_schema_change_is_major() -> None:
    """Modifying a response schema triggers a major impact."""

    old = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      responses:
        "200":
          content:
            application/json:
              schema:
                type: string
""",
    )
    new = _build(
        """
openapi: 3.0.0
paths:
  /pets:
    get:
      responses:
        "200":
          content:
            application/json:
              schema:
                type: integer
""",
    )
    impacts = diff_specs(old, new)
    assert any(
        i.severity == "major" and i.reason == "Changed response 200 schema"
        for i in impacts
    )
