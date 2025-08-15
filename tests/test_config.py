import builtins
import importlib

import tomli

from semverbump.config import load_config


def test_load_config_parses_analyzers(tmp_path):
    cfg_file = tmp_path / "semverbump.toml"
    cfg_file.write_text("[analyzers]\nflask_routes = true\nsqlalchemy = false\n")
    cfg = load_config(cfg_file)
    assert cfg.analyzers.enabled == {"flask_routes"}


def test_load_config_defaults_analyzers(tmp_path):
    cfg = load_config(tmp_path / "missing.toml")
    assert cfg.analyzers.enabled == set()


def test_tomli_fallback(monkeypatch, tmp_path):
    """Ensure ``tomli`` is used when ``tomllib`` is unavailable."""
    import semverbump.config as config

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
