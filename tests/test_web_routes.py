from bumpwright.analysers.web_routes import (diff_routes,
                                             extract_routes_from_source)


def _build(src: str):
    return extract_routes_from_source(src)


def test_removed_route_is_major():
    old = _build(
        """
from flask import Flask
app = Flask(__name__)

@app.route('/a')
def a():
    return 'ok'
"""
    )
    new = {}
    impacts = diff_routes(old, new)
    assert any(i.severity == "major" for i in impacts)


def test_param_optional_to_required_is_major():
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


def test_added_query_param_is_minor():
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
