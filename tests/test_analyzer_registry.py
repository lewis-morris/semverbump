from typing import List

import pytest

from bumpwright.analyzers import (
    Analyzer,
    AnalyzerNotFoundError,
    AnalyzerRegistrationError,
    get,
    register,
)
from bumpwright.compare import Impact
from bumpwright.config import Config


def test_register_duplicate_raises() -> None:
    @register("dummy_test_plugin")
    class Dummy(Analyzer):
        def __init__(self, cfg: Config) -> None:  # pragma: no cover - trivial
            pass

        def collect(self, ref: str) -> object:
            return None

        def compare(self, old: object, new: object) -> List[Impact]:
            return []

    with pytest.raises(AnalyzerRegistrationError):

        @register("dummy_test_plugin")
        class Duplicate(Dummy):  # pragma: no cover - registration only
            pass


def test_get_returns_registered_and_raises() -> None:
    @register("another_test_plugin", override=True)
    class Another(Analyzer):
        def __init__(self, cfg: Config) -> None:  # pragma: no cover - trivial
            pass

        def collect(self, ref: str) -> object:
            return None

        def compare(self, old: object, new: object) -> List[Impact]:
            return []

    assert get("another_test_plugin") is Another
    with pytest.raises(AnalyzerNotFoundError):
        get("missing_plugin")
