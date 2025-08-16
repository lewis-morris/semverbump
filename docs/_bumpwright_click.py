"""Click wrappers for documenting the :mod:`bumpwright` CLI."""

from __future__ import annotations

import argparse
import click
from bumpwright.cli.bump import bump_command
from bumpwright.cli.init import init_command


@click.group()
@click.option(
    "--config",
    default="bumpwright.toml",
    show_default=True,
    help="Path to configuration file. See :doc:`configuration` for details.",
)
@click.pass_context
def cli(ctx: click.Context, config: str) -> None:
    """Suggest and apply semantic version bumps."""

    ctx.obj = argparse.Namespace(config=config)


@cli.command()
@click.pass_obj
def init(args: argparse.Namespace) -> int:
    """Create baseline release commit."""

    return init_command(args)


@cli.command()
@click.option(
    "--level",
    type=click.Choice(["major", "minor", "patch"]),
    help="Desired bump level; if omitted, it is inferred from --base and --head.",
)
@click.option(
    "--base",
    help=(
        "Base git reference when auto-deciding the level. Defaults to the last release "
        "commit or the previous commit (HEAD^)."
    ),
)
@click.option("--head", default="HEAD", show_default=True, help="Head git reference.")
@click.option(
    "--format",
    "format_",
    type=click.Choice(["text", "md", "json"]),
    default="text",
    show_default=True,
    help="Output style: plain text, Markdown, or machine-readable JSON.",
)
@click.option(
    "--repo-url",
    help="Base repository URL for linking commit hashes in Markdown output.",
)
@click.option(
    "--decide",
    is_flag=True,
    help="Only determine the bump level without modifying any files.",
)
@click.option(
    "--enable-analyser",
    multiple=True,
    help="Enable analyser NAME (repeatable) in addition to configuration.",
)
@click.option(
    "--disable-analyser",
    multiple=True,
    help="Disable analyser NAME (repeatable) even if configured.",
)
@click.option(
    "--pyproject",
    default="pyproject.toml",
    show_default=True,
    help="Path to the project's pyproject.toml file.",
)
@click.option(
    "--version-path",
    multiple=True,
    help="Additional glob pattern for files containing the project version (repeatable).",
)
@click.option(
    "--version-ignore",
    multiple=True,
    help="Glob pattern for paths to exclude from version updates (repeatable).",
)
@click.option(
    "--commit", is_flag=True, help="Create a git commit for the version change."
)
@click.option("--tag", is_flag=True, help="Create a git tag for the new version.")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Display the new version without modifying any files.",
)
@click.option(
    "--changelog",
    type=str,
    help="Append release notes to FILE or stdout when no path is given.",
)
@click.option(
    "--changelog-template",
    type=str,
    help=("Jinja2 template file for changelog entries; defaults to built-in template."),
)
@click.pass_obj
def bump(args: argparse.Namespace, **kwargs: object) -> int:
    """Update project version metadata and optionally commit and tag the change."""

    params = vars(args).copy()
    params.update(kwargs)
    params["enable_analyser"] = list(params.get("enable_analyser", []))
    params["disable_analyser"] = list(params.get("disable_analyser", []))
    params["version_path"] = list(params.get("version_path", []))
    params["version_ignore"] = list(params.get("version_ignore", []))
    params["format"] = params.pop("format_")
    return bump_command(argparse.Namespace(**params))
