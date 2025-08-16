import logging
import os
import subprocess
from pathlib import Path

from bumpwright.analysers import load_enabled
from bumpwright.analysers.cli import CLIAnalyser, diff_cli, extract_cli_from_source
from bumpwright.cli.decide import _run_analysers
from bumpwright.compare import Impact
from bumpwright.config import Config, Ignore, Project


def _build(src: str):
    return extract_cli_from_source(src)


def test_removed_command_major():
    old = _build(
        """
import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
p_run = sub.add_parser('run')
p_build = sub.add_parser('build')
"""
    )
    new = _build(
        """
import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
p_build = sub.add_parser('build')
"""
    )
    impacts = diff_cli(old, new)
    assert impacts == [Impact("major", "run", "Removed command")]


def test_added_optional_flag_minor():
    old = _build(
        """
import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
p_run = sub.add_parser('run')
"""
    )
    new = _build(
        """
import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
p_run = sub.add_parser('run')
p_run.add_argument('--force')
"""
    )
    impacts = diff_cli(old, new)
    assert impacts == [Impact("minor", "run", "Added optional option '--force'")]


def test_click_required_change_major():
    old = _build(
        """
import click

@click.command()
@click.option('--name')
def cli(name):
    pass
"""
    )
    new = _build(
        """
import click

@click.command()
@click.option('--name', required=True)
def cli(name):
    pass
"""
    )
    impacts = diff_cli(old, new)
    assert impacts == [Impact("major", "cli", "Option '--name' became required")]


def test_async_click_command_detected():
    cmds = _build(
        """
import click

@click.command()
async def cli():
    pass
"""
    )
    assert "cli" in cmds


def test_argparse_nargs_plus_major():
    old = _build(
        """
import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
p_run = sub.add_parser('run')
p_run.add_argument('--files')
"""
    )
    new = _build(
        """
import argparse
parser = argparse.ArgumentParser()
sub = parser.add_subparsers()
p_run = sub.add_parser('run')
p_run.add_argument('--files', nargs='+')
"""
    )
    impacts = diff_cli(old, new)
    assert impacts == [Impact("major", "run", "Option '--files' became required")]


def _run(cmd: list[str], cwd: Path) -> str:
    res = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return res.stdout.strip()


def test_cli_analyser_respects_ignore(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init"], repo)
    _run(["git", "config", "user.email", "a@b.c"], repo)
    _run(["git", "config", "user.name", "tester"], repo)
    (repo / "main.py").write_text(
        """
import click

@click.command()
def a():
    pass
"""
    )
    _run(["git", "add", "main.py"], repo)
    _run(["git", "commit", "-m", "base"], repo)
    base = _run(["git", "rev-parse", "HEAD"], repo)

    (repo / "tests").mkdir()
    (repo / "tests" / "cli.py").write_text(
        """
import click

@click.command()
def b():
    pass
"""
    )
    _run(["git", "add", "tests"], repo)
    _run(["git", "commit", "-m", "add ignored"], repo)
    head = _run(["git", "rev-parse", "HEAD"], repo)

    cfg = Config(project=Project(public_roots=["."]), ignore=Ignore(paths=["tests/**"]))
    analyser = CLIAnalyser(cfg)
    old_cwd = os.getcwd()
    os.chdir(repo)
    try:
        old = analyser.collect(base)
        new = analyser.collect(head)
    finally:
        os.chdir(old_cwd)
    impacts = analyser.compare(old, new)
    assert impacts == []


def test_load_enabled_instantiates_plugins() -> None:
    cfg = Config()
    cfg.analysers.enabled.add("cli")
    analysers = load_enabled(cfg)
    assert [type(a) for a in analysers] == [CLIAnalyser]


def test_run_analysers_warns_for_unknown(caplog) -> None:
    cfg = Config()
    with caplog.at_level(logging.WARNING):
        impacts = _run_analysers("base", "head", cfg, enable=["unknown"])  # no analyser
    assert impacts == []
    assert "Analyser 'unknown' is not registered" in caplog.text
