from semverbump.compare import compare_funcs, decide_bump, diff_public_api
from semverbump.public_api import FuncSig, Param



def _sig(name, params, returns=None):
    return FuncSig(name, tuple(params), returns)


def _p(name, kind="pos", default=None, ann=None):
    return Param(name, kind, default, ann)


def test_added_optional_param_is_minor():
    old = _sig("m:f", [_p("x")], "-> int")
    new = _sig("m:f", [_p("x"), _p("timeout", kind="kwonly", default="None")], "-> int")
    impacts = compare_funcs(old, new)
    assert any(i.severity == "minor" for i in impacts)


def test_removed_required_param_is_major():
    old = _sig("m:f", [_p("x"), _p("y")], None)
    new = _sig("m:f", [_p("x")], None)
    impacts = compare_funcs(old, new)
    assert any(i.severity == "major" for i in impacts)


def test_removed_symbol_is_major():
    old = {"m:f": _sig("m:f", [_p("x")], None)}
    new = {}
    impacts = diff_public_api(old, new)
    assert any(i.severity == "major" for i in impacts)
    assert decide_bump(impacts) == "major"
