"""Tests for public API comparison helpers."""

from bumpwright.compare import (
    Impact,
    Severity,
    compare_funcs,
    decide_bump,
    diff_public_api,
)
from bumpwright.public_api import FuncSig, Param

MAJOR: Severity = "major"
MINOR: Severity = "minor"
CONFIDENCE_HALF = 0.5


def _sig(name, params, returns=None):
    return FuncSig(name, tuple(params), returns)


def _p(name, kind="pos", default=None, ann=None):
    return Param(name, kind, default, ann)


def test_added_optional_param_is_minor():
    old = _sig("m:f", [_p("x")], "-> int")
    new = _sig("m:f", [_p("x"), _p("timeout", kind="kwonly", default="None")], "-> int")
    impacts = compare_funcs(old, new)
    assert any(i.severity == MINOR for i in impacts)


def test_added_required_param_is_major():
    old = _sig("m:f", [_p("x")], "-> int")
    new = _sig("m:f", [_p("x"), _p("y")], "-> int")
    impacts = compare_funcs(old, new)
    assert any(i.severity == MAJOR for i in impacts)


def test_removed_required_param_is_major():
    old = _sig("m:f", [_p("x"), _p("y")], None)
    new = _sig("m:f", [_p("x")], None)
    impacts = compare_funcs(old, new)
    assert any(i.severity == MAJOR for i in impacts)


def test_removed_optional_param_is_minor():
    old = _sig(
        "m:f",
        [_p("x"), _p("timeout", kind="kwonly", default="None")],
        "-> int",
    )
    new = _sig("m:f", [_p("x")], "-> int")
    impacts = compare_funcs(old, new)
    assert any(i.severity == MINOR for i in impacts)


def test_removed_symbol_is_major():
    old = {"m:f": _sig("m:f", [_p("x")], None)}
    new = {}
    impacts = diff_public_api(old, new)
    assert any(i.severity == MAJOR for i in impacts)
    decision = decide_bump(impacts)
    assert decision.level == MAJOR
    assert decision.confidence == 1.0
    assert decision.reasons == ["Removed public symbol"]


def test_confidence_ratio():
    old = {"m:f": _sig("m:f", [_p("x")], None)}
    new = {"m:f": _sig("m:f", [_p("x"), _p("y")], None)}
    impacts = diff_public_api(old, new)
    impacts.append(Impact(MINOR, "m:g", "Added public symbol"))
    decision = decide_bump(impacts)
    assert decision.level == MAJOR
    assert decision.confidence == CONFIDENCE_HALF
    assert decision.reasons == ["Added required param 'y'"]
