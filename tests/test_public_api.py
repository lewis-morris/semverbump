from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "bumpwright.public_api",
    Path(__file__).resolve().parents[1] / "bumpwright" / "public_api.py",
)
public_api = importlib.util.module_from_spec(spec)
sys.modules["bumpwright.public_api"] = public_api
assert spec.loader  # noqa: PT018 - ensure loader exists for mypy
spec.loader.exec_module(public_api)
extract_public_api_from_source = public_api.extract_public_api_from_source
module_name_from_path = public_api.module_name_from_path


def test_extracts_functions_and_methods():
    code = """
__all__ = ["foo", "Bar"]
def foo(x: int, y: int = 1) -> int: return x + y
def _hidden(): pass
class Bar:
    def baz(self, q, *, opt=None) -> str: return "ok"
    def _private(self): pass
"""
    api = extract_public_api_from_source("pkg.mod", code)
    keys = set(api.keys())
    assert "pkg.mod:foo" in keys
    assert "pkg.mod:Bar.baz" in keys
    assert "pkg.mod:_hidden" not in keys
    assert "pkg.mod:Bar._private" not in keys

    foo = api["pkg.mod:foo"]
    assert foo.returns == "-> int" or foo.returns.endswith(
        "int"
    )  # libcst emits "-> int" style string
    assert any(p.name == "y" and p.default is not None for p in foo.params)


def test_respects_class_exports():
    code = """
__all__ = ["Visible"]
class Visible:
    def ping(self):
        pass
class Hidden:
    def ping(self):
        pass
"""
    api = extract_public_api_from_source("pkg.mod", code)
    keys = set(api.keys())
    assert "pkg.mod:Visible.ping" in keys
    assert "pkg.mod:Hidden.ping" not in keys


def test_module_name_from_path_nested(tmp_path):
    root = tmp_path / "pkg"
    path = root / "a" / "b" / "mod.py"
    assert module_name_from_path(str(root), str(path)) == "a.b.mod"


def test_module_name_from_path_outside_root(tmp_path):
    root = tmp_path / "pkg"
    path = tmp_path / "other" / "mod.py"
    with pytest.raises(ValueError):
        module_name_from_path(str(root), str(path))


def test_param_kinds():
    code = """
def sample(a, /, b, c=1, *d, e, f=2, **g):
    pass
"""
    api = extract_public_api_from_source("pkg.mod", code)
    params = api["pkg.mod:sample"].params
    assert [(p.name, p.kind, p.default) for p in params] == [
        ("a", "posonly", None),
        ("b", "pos", None),
        ("c", "pos", "1"),
        ("d", "vararg", None),
        ("e", "kwonly", None),
        ("f", "kwonly", "2"),
        ("g", "varkw", None),
    ]


def test_extract_without_exports_includes_public() -> None:
    """Include public symbols when ``__all__`` is absent."""

    code = """
def foo():
    pass
def _bar():
    pass
"""
    api = extract_public_api_from_source("pkg.mod", code)
    assert "pkg.mod:foo" in api
    assert "pkg.mod:_bar" not in api


def test_extract_invalid_code_raises() -> None:
    """Raise ``SyntaxError`` when source cannot be parsed."""

    with pytest.raises(SyntaxError):
        extract_public_api_from_source("pkg.mod", "def bad(:\n pass")


@pytest.mark.parametrize(
    "prefix",
    [
        "__all__ = ['foo'] + ['bar']",
        "names = ['foo']\nextra = ['bar']\n__all__ = names + extra",
    ],
)
def test_extracts_all_from_concatenation(prefix: str) -> None:
    """Detect ``__all__`` constructed via simple concatenation."""

    code = f"""
{prefix}
def foo():
    pass
def bar():
    pass
"""
    api = extract_public_api_from_source("pkg.mod", code)
    keys = set(api.keys())
    assert {"pkg.mod:foo", "pkg.mod:bar"} == keys
