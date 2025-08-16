from __future__ import annotations

from bumpwright import analyzers
from bumpwright.analyzers import AnalyzerInfo
from bumpwright.cli import _run_analyzers
from bumpwright.compare import Impact
from bumpwright.config import Config


class DummyAnalyzer:
    """Trivial analyzer used for flag tests."""

    def __init__(self, cfg: Config) -> None:  # pragma: no cover - trivial
        """Store configuration for later use."""

        self.cfg = cfg

    def collect(self, ref: str) -> str:  # pragma: no cover - trivial
        """Return the provided reference."""

        return ref

    def compare(self, old: str, new: str) -> list[Impact]:  # pragma: no cover - trivial
        """Produce a constant impact for testing."""

        return [Impact("warn", "dummy", "ran")]


def _register_dummy(monkeypatch) -> None:
    monkeypatch.setattr(
        analyzers,
        "REGISTRY",
        {"dummy": AnalyzerInfo(name="dummy", cls=DummyAnalyzer, description="")},
    )


def test_enable_flag_overrides_config(monkeypatch) -> None:
    _register_dummy(monkeypatch)
    cfg = Config()
    impacts = _run_analyzers("base", "head", cfg, enable=["dummy"])
    assert any(i.symbol == "dummy" for i in impacts)


def test_disable_flag_overrides_config(monkeypatch) -> None:
    _register_dummy(monkeypatch)
    cfg = Config()
    cfg.analyzers.enabled.add("dummy")
    impacts = _run_analyzers("base", "head", cfg, disable=["dummy"])
    assert not impacts
