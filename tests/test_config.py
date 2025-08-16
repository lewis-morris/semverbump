import builtins
import importlib
from pathlib import Path

import tomli

from bumpwright.config import load_config


def test_load_config_parses_analyzers(tmp_path: Path) -> None:
    cfg_file = tmp_path / "bumpwright.toml"
    cfg_file.write_text("[analyzers]\nflask_routes = true\nsqlalchemy = false\n")
    cfg = load_config(cfg_file)
    assert cfg.analyzers.enabled == {"flask_routes"}


def test_load_config_defaults_analyzers(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.toml")
    assert cfg.analyzers.enabled == set()


def test_load_config_changelog(tmp_path: Path) -> None:
    cfg_file = tmp_path / "bumpwright.toml"
    cfg_file.write_text("[changelog]\npath='NEWS.md'\n")
    cfg = load_config(cfg_file)
    assert cfg.changelog.path == "NEWS.md"


def test_load_config_changelog_default(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.toml")
    assert cfg.changelog.path == ""


def test_tomli_fallback(monkeypatch, tmp_path: Path) -> None:
    """Ensure ``tomli`` is used when ``tomllib`` is unavailable."""
    from bumpwright import config

    original_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "tomllib":  # Simulate missing stdlib module
            raise ModuleNotFoundError
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    importlib.reload(config)

    assert config.tomllib is tomli
    cfg = config.load_config(tmp_path / "missing.toml")
    assert cfg.project.index_file == "pyproject.toml"


def test_mutating_config_does_not_alter_defaults(tmp_path: Path) -> None:
    """Ensure modifying a loaded config leaves defaults unchanged."""

    cfg = load_config(tmp_path / "missing.toml")
    cfg.project.public_roots.append("src")

    import bumpwright.config as config_module

    fresh = load_config(tmp_path / "missing.toml")
    assert config_module._DEFAULTS["project"]["public_roots"] == ["."]
    assert fresh.project.public_roots == ["."]
