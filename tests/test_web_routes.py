from __future__ import annotations

from bumpwright.analysers.web_routes import (
    Route,
    diff_routes,
    extract_routes_from_source,
)


def _build(src: str) -> dict[tuple[str, str], Route]:
    """Parse source code into a route mapping."""

    return extract_routes_from_source(src)


def test_removed_route_is_major() -> None:
    """Removing an existing route triggers a major impact."""

    old = _build(
        """
from flask import Flask
app = Flask(__name__)

@app.route('/a')
def a():
    return 'ok'
"""
    )
    new: dict[tuple[str, str], Route] = {}
    impacts = diff_routes(old, new)
    assert any(i.severity == "major" for i in impacts)


def test_param_optional_to_required_is_major() -> None:
    """Making an optional parameter required is a major impact."""

    old = _build(
        """
from fastapi import FastAPI
app = FastAPI()

@app.get('/a')
def a(q: int | None = None):
    return q
"""
    )
    new = _build(
        """
from fastapi import FastAPI
app = FastAPI()

@app.get('/a')
def a(q: int):
    return q
"""
    )
    impacts = diff_routes(old, new)
    assert any(i.severity == "major" for i in impacts)


def test_added_query_param_is_minor() -> None:
    """Adding an optional query parameter is a minor impact."""

    old = _build(
        """
from fastapi import FastAPI
app = FastAPI()

@app.get('/a')
def a():
    return 1
"""
    )
    new = _build(
        """
from fastapi import FastAPI
app = FastAPI()

@app.get('/a')
def a(limit: int | None = None):
    return 1
"""
    )
    impacts = diff_routes(old, new)
    assert any(i.severity == "minor" for i in impacts)


def test_async_route_detected() -> None:
    """Async routes should still be detected."""

    routes = _build(
        """
from fastapi import FastAPI
app = FastAPI()

@app.get('/a')
async def a():
    return 1
"""
    )
    assert ("/a", "GET") in routes


def test_flask_multiple_methods_extracted() -> None:
    """Flask routes with multiple methods should produce entries per method."""

    routes = _build(
        """
from flask import Flask
app = Flask(__name__)

@app.route("/a", methods=["POST", "PUT"])
def a():
    return "ok"
"""
    )
    assert ("/a", "POST") in routes
    assert ("/a", "PUT") in routes
