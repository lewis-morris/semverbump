from semverbump.analyzers.cli import diff_cli, extract_cli_from_source


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
