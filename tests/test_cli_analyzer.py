import os
import subprocess
from pathlib import Path

from bumpwright.analyzers import load_enabled
from bumpwright.analyzers.cli import CLIAnalyzer, diff_cli, extract_cli_from_source
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
    assert any(i.severity == "major" for i in impacts)


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
    assert any(i.severity == "minor" for i in impacts)


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
    assert any(i.severity == "major" for i in impacts)


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
    assert any(i.severity == "major" for i in impacts)


def _run(cmd: list[str], cwd: Path) -> str:
    res = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return res.stdout.strip()


def test_cli_analyzer_respects_ignore(tmp_path: Path) -> None:
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
    analyzer = CLIAnalyzer(cfg)
    old_cwd = os.getcwd()
    os.chdir(repo)
    try:
        old = analyzer.collect(base)
        new = analyzer.collect(head)
    finally:
        os.chdir(old_cwd)
    impacts = analyzer.compare(old, new)
    assert impacts == []


def test_load_enabled_instantiates_plugins() -> None:
    cfg = Config()
    cfg.analyzers.enabled.add("cli")
    analyzers = load_enabled(cfg)
    assert any(isinstance(a, CLIAnalyzer) for a in analyzers)
