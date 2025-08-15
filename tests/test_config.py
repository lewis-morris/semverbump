from semverbump.config import load_config


def test_load_config_parses_analyzers(tmp_path):
    cfg_file = tmp_path / "semverbump.toml"
    cfg_file.write_text("[analyzers]\nflask_routes = true\nsqlalchemy = false\n")
    cfg = load_config(cfg_file)
    assert cfg.analyzers.enabled == {"flask_routes"}


def test_load_config_defaults_analyzers(tmp_path):
    cfg = load_config(tmp_path / "missing.toml")
    assert cfg.analyzers.enabled == set()
