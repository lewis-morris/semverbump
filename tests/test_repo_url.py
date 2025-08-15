import argparse
import os
from pathlib import Path

from bumpwright.cli import decide_command
from bumpwright.compare import Impact
from tests.cli_helpers import setup_repo


def test_repo_url_links_commits(tmp_path: Path, monkeypatch, capsys) -> None:
    repo, _pkg, base = setup_repo(tmp_path)
    commit_hash = base

    # Avoid real git interactions in decide_command
    monkeypatch.setattr("bumpwright.cli._build_api_at_ref", lambda *a, **k: {})
    monkeypatch.setattr("bumpwright.cli.diff_public_api", lambda *a, **k: [])
    monkeypatch.setattr(
        "bumpwright.cli._run_analyzers",
        lambda *a, **k: [Impact("minor", "sym", f"ref {commit_hash}")],
    )

    args = argparse.Namespace(
        config="bumpwright.toml",
        base=base,
        head="HEAD",
        format="md",
        repo_url="https://github.com/example/repo",
    )

    old_cwd = os.getcwd()
    os.chdir(repo)
    try:
        decide_command(args)
    finally:
        os.chdir(old_cwd)

    output = capsys.readouterr().out
    link = f"[{commit_hash}](https://github.com/example/repo/commit/{commit_hash})"
    assert link in output
