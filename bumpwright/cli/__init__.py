"""Command-line interface for the :mod:`bumpwright` project."""

from __future__ import annotations

import argparse
import sys

from ..analysers import available


def add_ref_options(parser: argparse.ArgumentParser) -> None:
    """Attach git reference options to ``parser``.

    Args:
        parser: Subparser to which the ``--base`` and ``--head`` options are added.
    """

    parser.add_argument(
        "--base",
        help=(
            "Base git reference when auto-deciding the level. Defaults to the last release "
            "commit or the previous commit (HEAD^)."
        ),
    )
    parser.add_argument(
        "--head",
        default="HEAD",
        help="Head git reference; defaults to the current HEAD.",
    )


def add_analyser_toggles(parser: argparse.ArgumentParser) -> None:
    """Attach analyser enable/disable flags to ``parser``.

    Args:
        parser: Subparser receiving analyser toggling options.
    """

    parser.add_argument(
        "--enable-analyser",
        action="append",
        dest="enable_analyser",
        help="Enable analyser NAME (repeatable) in addition to configuration.",
    )
    parser.add_argument(
        "--disable-analyser",
        action="append",
        dest="disable_analyser",
        help="Disable analyser NAME (repeatable) even if configured.",
    )


from .bump import bump_command  # noqa: E402
from .init import init_command  # noqa: E402


def get_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the command-line interface."""

    avail = ", ".join(available()) or "none"
    parser = argparse.ArgumentParser(
        prog="bumpwright",
        description=(
            f"Suggest and apply semantic version bumps. Available analysers: {avail}."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default="bumpwright.toml",
        help="Path to configuration file.",
    )

    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser(
        "init",
        help="Create baseline release commit",
        description=(
            "Create an empty 'chore(release): initialise baseline' commit to "
            "establish a comparison point for future bumps."
        ),
    )
    p_init.set_defaults(func=init_command)

    p_bump = sub.add_parser(
        "bump",
        help="Apply a version bump",
        description="Update project version metadata and optionally commit and tag the change.",
    )
    p_bump.add_argument(
        "--level",
        choices=["major", "minor", "patch"],
        help="Desired bump level; if omitted, it is inferred from --base and --head.",
    )
    add_ref_options(p_bump)
    p_bump.add_argument(
        "--format",
        choices=["text", "md", "json"],
        default="text",
        help="Output style: plain text, Markdown, or machine-readable JSON.",
    )
    p_bump.add_argument(
        "--repo-url",
        help="Base repository URL for linking commit hashes in Markdown output.",
    )
    p_bump.add_argument(
        "--decide",
        action="store_true",
        help="Only determine the bump level without modifying any files.",
    )
    add_analyser_toggles(p_bump)
    p_bump.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to the project's pyproject.toml file.",
    )
    p_bump.add_argument(
        "--version-path",
        action="append",
        dest="version_path",
        help=(
            "Additional glob pattern for files containing the project version "
            "(repeatable). Defaults include pyproject.toml, setup.py, setup.cfg, "
            "and any __init__.py, version.py, or _version.py files."
        ),
    )
    p_bump.add_argument(
        "--version-ignore",
        action="append",
        dest="version_ignore",
        help=("Glob pattern for paths to exclude from version updates (repeatable)."),
    )
    p_bump.add_argument(
        "--commit",
        action="store_true",
        help="Create a git commit for the version change.",
    )
    p_bump.add_argument(
        "--tag", action="store_true", help="Create a git tag for the new version."
    )
    p_bump.add_argument(
        "--dry-run",
        action="store_true",
        help="Display the new version without modifying any files.",
    )
    p_bump.add_argument(
        "--changelog",
        nargs="?",
        const="-",
        help="Append release notes to FILE or stdout when no path is given.",
    )
    p_bump.add_argument(
        "--changelog-template",
        help="Jinja2 template file for changelog entries; defaults to built-in template.",
    )
    p_bump.set_defaults(func=bump_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``bumpwright`` CLI."""

    parser = get_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
