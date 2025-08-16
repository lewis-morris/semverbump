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
    """Suggest and apply semantic version bumps.

    Args:
        ctx: Click execution context.
        config: Path to the configuration file used for the run. Defaults to
            ``bumpwright.toml``.
    """

    ctx.obj = argparse.Namespace(config=config)


@cli.command()
@click.pass_obj
def init(args: argparse.Namespace) -> int:
    """Create a baseline release commit.

    Args:
        args: Parsed command-line arguments from :func:`cli`.

    Returns:
        Exit status code, where ``0`` indicates success and ``1`` an error.
    """

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
    help=(
        "Additional glob pattern for files containing the project version "
        "(repeatable). Defaults include ``pyproject.toml``, ``setup.py``, "
        "``setup.cfg``, and any ``__init__.py``, ``version.py``, or "
        "``_version.py`` files."
    ),
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
    flag_value="-",
    default=None,
    nargs=1,
    is_flag=False,
    metavar="[FILE]",
    help="Append release notes to FILE or stdout when no path is given.",
)
@click.option(
    "--changelog-template",
    type=str,
    help=("Jinja2 template file for changelog entries; defaults to built-in template."),
)
@click.option(
    "--changelog-exclude",
    multiple=True,
    help=(
        "Regex pattern for commit subjects to exclude from changelog " "(repeatable)."
    ),
)
@click.pass_obj
def bump(args: argparse.Namespace, **kwargs: object) -> int:
    """Update version metadata and optionally commit and tag the change.

    Args:
        args: Parsed command-line arguments from :func:`cli`.
        **kwargs: Command-specific options. Notable parameters include:

            level (str | None): Desired bump level, one of ``major``, ``minor``,
            or ``patch``. If omitted the level is inferred from repository
            history.

            base (str | None): Git reference used as the comparison base when
            inferring the bump level. Defaults to the latest release commit or
            ``HEAD^``.

            head (str): Git reference representing the working tree. Defaults
            to ``HEAD``.

            format_ (str): Output format: ``text`` (default), ``md`` for
            Markdown, or ``json`` for machine-readable output.

            repo_url (str | None): Base repository URL used to build commit
            links in Markdown output.

            decide (bool): When ``True``, only report the bump level without
            modifying any files.

            enable_analyser (tuple[str, ...]): Names of analysers to enable in
            addition to those configured.

            disable_analyser (tuple[str, ...]): Names of analysers to disable
            even if configured.

            pyproject (str): Path to ``pyproject.toml``. Defaults to
            ``pyproject.toml``.

            version_path (tuple[str, ...]): Extra glob patterns for files whose
            version fields should be updated. Defaults include
            ``pyproject.toml``, ``setup.py``, ``setup.cfg``, and any
            ``__init__.py``, ``version.py``, or ``_version.py`` files.

            version_ignore (tuple[str, ...]): Glob patterns for paths to exclude
            from version updates.

            commit (bool): Create a git commit containing the version change.

            tag (bool): Create a git tag for the new version.

            dry_run (bool): Show the new version without modifying files.

            changelog (str | None): Write release notes to the given file or
            stdout when ``-`` is provided.

            changelog_template (str | None): Path to a Jinja2 template used to
            render changelog entries. Defaults to the built-in template.

            changelog_exclude (tuple[str, ...]): Regex patterns of commit
            subjects to omit from changelog entries.

    Returns:
        Exit status code, where ``0`` indicates success and ``1`` an error.
    """

    params = vars(args).copy()
    params.update(kwargs)
    params["enable_analyser"] = list(params.get("enable_analyser", []))
    params["disable_analyser"] = list(params.get("disable_analyser", []))
    params["version_path"] = list(params.get("version_path", []))
    params["version_ignore"] = list(params.get("version_ignore", []))
    params["changelog_exclude"] = list(params.get("changelog_exclude", []))
    params["format"] = params.pop("format_")
    return bump_command(argparse.Namespace(**params))
