import argparse

import click

from semverbump.analyzers.cli import diff_cli, extract_cli


def _argparse_v1() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    run = sub.add_parser("run")
    run.add_argument("--force", action="store_true")
    return parser


def _argparse_v2_optional() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    run = sub.add_parser("run")
    run.add_argument("--force", action="store_true")
    run.add_argument("--verbose", action="store_true")
    return parser


def _argparse_v2_removed_cmd() -> argparse.ArgumentParser:
    return argparse.ArgumentParser()


def _click_v1() -> click.Group:
    @click.group()
    def cli() -> None:
        """Top level."""

    @cli.command()
    @click.option("--force", is_flag=True)
    def build(force: bool) -> None:  # pragma: no cover - runtime check
        pass

    return cli


def _click_v2_required() -> click.Group:
    @click.group()
    def cli() -> None:
        """Top level."""

    @cli.command()
    @click.option("--force", is_flag=True)
    @click.option("--config", required=True)
    def build(force: bool, config: str) -> None:  # pragma: no cover - runtime check
        pass

    return cli


def test_added_optional_flag_is_minor() -> None:
    old = extract_cli(_argparse_v1())
    new = extract_cli(_argparse_v2_optional())
    impacts = diff_cli(old, new)
    assert any(i.severity == "minor" for i in impacts)


def test_removed_command_is_major() -> None:
    old = extract_cli(_argparse_v1())
    new = extract_cli(_argparse_v2_removed_cmd())
    impacts = diff_cli(old, new)
    assert any(i.severity == "major" for i in impacts)


def test_added_required_option_is_major_click() -> None:
    old = extract_cli(_click_v1())
    new = extract_cli(_click_v2_required())
    impacts = diff_cli(old, new)
    assert any(i.severity == "major" for i in impacts)
