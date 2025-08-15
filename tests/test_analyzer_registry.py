import pytest

from bumpwright.analyzers import (
    Analyzer,
    available,
    get_analyzer_info,
    load_enabled,
    register,
)
from bumpwright.compare import Impact
from bumpwright.config import Config


def test_register_records_metadata(monkeypatch) -> None:
    """Ensure register stores class and description."""
    from bumpwright import analyzers

    monkeypatch.setattr(analyzers, "REGISTRY", {})

    @register("dummy", "Example analyzer")
    class DummyAnalyzer(Analyzer):
        def __init__(self, cfg: Config) -> None:  # pragma: no cover - simple init
            self.cfg = cfg

        def collect(self, ref: str) -> object:  # pragma: no cover - trivial
            return {}

        def compare(
            self, old: object, new: object
        ) -> list[Impact]:  # pragma: no cover - trivial
            return []

    assert "dummy" in available()
    info = get_analyzer_info("dummy")
    assert info and info.description == "Example analyzer"


def test_load_enabled_errors_for_unknown(monkeypatch) -> None:
    """Unknown analyzers should raise a clear error."""
    from bumpwright import analyzers

    monkeypatch.setattr(analyzers, "REGISTRY", {})
    cfg = Config()
    cfg.analyzers.enabled.add("missing")
    with pytest.raises(ValueError):
        load_enabled(cfg)
