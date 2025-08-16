"""Tests for public API comparison helpers."""

from bumpwright.compare import (
    Impact,
    _added_params,
    _param_annotation_changes,
    _param_default_changes,
    _param_kind_changes,
    _removed_params,
    _return_annotation_change,
    compare_funcs,
    decide_bump,
    diff_public_api,
)
from bumpwright.public_api import FuncSig, Param
from bumpwright.types import BumpLevel

MAJOR: BumpLevel = "major"
MINOR: BumpLevel = "minor"
CONFIDENCE_HALF = 0.5


def _sig(name, params, returns=None):
    return FuncSig(name, tuple(params), returns)


def _p(name, kind="pos", default=None, ann=None):
    return Param(name, kind, default, ann)


def test_removed_params_classify_optional_and_required():
    old = _sig(
        "m:f",
        [_p("x"), _p("timeout", kind="kwonly", default="None")],
        "-> int",
    )
    new = _sig("m:f", [], "-> int")
    impacts = _removed_params({p.name: p for p in old.params}, {p.name: p for p in new.params}, "m:f")
    assert Impact(MAJOR, "m:f", "Removed required param 'x'") in impacts
    assert Impact(MINOR, "m:f", "Removed optional param 'timeout'") in impacts


def test_added_params_classify_optional_and_required():
    old = _sig("m:f", [_p("x")], "-> int")
    new = _sig(
        "m:f",
        [_p("x"), _p("y"), _p("timeout", kind="kwonly", default="None")],
        "-> int",
    )
    impacts = _added_params({p.name: p for p in old.params}, {p.name: p for p in new.params}, "m:f")
    assert Impact(MAJOR, "m:f", "Added required param 'y'") in impacts
    assert Impact(MINOR, "m:f", "Added optional param 'timeout'") in impacts


def test_param_kind_changes_detected():
    old = _sig("m:f", [_p("x"), _p("y")], "-> int")
    new = _sig("m:f", [_p("x", kind="kwonly"), _p("y", kind="posonly")], "-> int")
    impacts = _param_kind_changes({p.name: p for p in old.params}, {p.name: p for p in new.params}, "m:f")
    assert Impact(MAJOR, "m:f", "Param 'x' kind changed pos→kwonly") in impacts
    assert Impact(MAJOR, "m:f", "Param 'y' kind changed pos→posonly") in impacts


def test_param_default_changes_detected():
    old = _sig(
        "m:f",
        [_p("x", default="1"), _p("y"), _p("z", default="1")],
        "-> int",
    )
    new = _sig(
        "m:f",
        [_p("x"), _p("y", default="2"), _p("z", default="2")],
        "-> int",
    )
    impacts = _param_default_changes({p.name: p for p in old.params}, {p.name: p for p in new.params}, "m:f")
    assert Impact(MAJOR, "m:f", "Param 'x' default removed") in impacts
    assert Impact(MINOR, "m:f", "Param 'y' default added") in impacts
    assert Impact(MINOR, "m:f", "Param 'z' default changed 1→2") in impacts


def test_param_annotation_changes_detected():
    old = _sig(
        "m:f",
        [_p("x", ann="int"), _p("y", ann="int"), _p("z")],
        "-> int",
    )
    new = _sig(
        "m:f",
        [_p("x"), _p("y", ann="str"), _p("z", ann="int")],
        "-> int",
    )
    impacts = _param_annotation_changes(
        {p.name: p for p in old.params},
        {p.name: p for p in new.params},
        "m:f",
        MINOR,
    )
    assert Impact(MINOR, "m:f", "Param 'x' annotation removed") in impacts
    assert Impact(MINOR, "m:f", "Param 'y' annotation changed int→str") in impacts
    assert Impact(MINOR, "m:f", "Param 'z' annotation added") in impacts


def test_return_annotation_change_helper():
    old = _sig("m:f", [_p("x")], "int")
    new = _sig("m:f", [_p("x")], "str")
    impacts = _return_annotation_change(old, new, MAJOR)
    assert impacts == [Impact(MAJOR, "m:f", "Return annotation changed")]


def test_return_annotation_change_helper_no_change():
    sig = _sig("m:f", [_p("x")], "int")
    assert _return_annotation_change(sig, sig, MAJOR) == []


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


def test_compare_funcs_no_changes():
    sig = _sig("m:f", [_p("x")], None)
    assert compare_funcs(sig, sig) == []


def test_compare_funcs_return_type_change_major():
    old = _sig("m:f", [_p("x")], "int")
    new = _sig("m:f", [_p("x")], "str")
    impacts = compare_funcs(old, new, return_type_change=MAJOR)
    assert impacts == [Impact(MAJOR, "m:f", "Return annotation changed")]


def test_compare_funcs_default_changes():
    old = _sig(
        "m:f",
        [_p("x", default="1"), _p("y"), _p("z", default="1")],
        None,
    )
    new = _sig(
        "m:f",
        [_p("x"), _p("y", default="2"), _p("z", default="2")],
        None,
    )
    impacts = compare_funcs(old, new)
    assert Impact(MAJOR, "m:f", "Param 'x' default removed") in impacts
    assert Impact(MINOR, "m:f", "Param 'y' default added") in impacts
    assert Impact(MINOR, "m:f", "Param 'z' default changed 1→2") in impacts


def test_compare_funcs_param_annotation_change():
    old = _sig("m:f", [_p("x", ann="int")], None)
    new = _sig("m:f", [_p("x", ann="str")], None)
    impacts = compare_funcs(old, new, param_annotation_change=MINOR)
    assert impacts == [Impact(MINOR, "m:f", "Param 'x' annotation changed int→str")]


def test_diff_public_api_added_symbol():
    new = {"m:f": _sig("m:f", [_p("x")], None)}
    impacts = diff_public_api({}, new)
    assert impacts == [Impact(MINOR, "m:f", "Added public symbol")]


def test_diff_public_api_no_changes():
    sig = _sig("m:f", [_p("x")], None)
    assert diff_public_api({"m:f": sig}, {"m:f": sig}) == []


def test_decide_bump_no_impacts():
    decision = decide_bump([])
    assert decision.level is None
    assert decision.confidence == 0.0
    assert decision.reasons == []
