from bumpwright.public_api import extract_public_api_from_source


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
