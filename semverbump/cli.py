"""Command-line interface for the :mod:`semverbump` project.

This module exposes subcommands for suggesting and applying semantic version
bumps based on public API differences and additional analyzers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List

from .analyzers import available, load_enabled
from .compare import Impact, decide_bump, diff_public_api
from .config import Config, load_config
from .gitutils import list_py_files_at_ref, read_file_at_ref
from .public_api import PublicAPI, extract_public_api_from_source, module_name_from_path
from .versioning import apply_bump, find_pyproject


def _build_api_at_ref(ref: str, roots: list[str], ignores: Iterable[str]) -> PublicAPI:
    """Collect the public API for ``roots`` at a git reference.

    Args:
        ref: Git reference to inspect.
        roots: Project root directories to scan.
        ignores: Glob patterns for paths to skip.

    Returns:
        Mapping of public symbols to signatures.
    """

    api: PublicAPI = {}
    for root in roots:
        for path in sorted(list_py_files_at_ref(ref, [root], ignore_globs=ignores)):
            code = read_file_at_ref(ref, path)
            if code is None:
                continue
            modname = module_name_from_path(root, path)
            api.update(extract_public_api_from_source(modname, code))
    return api


def _format_impacts_text(impacts: List[Impact]) -> str:
    """Render a list of impacts as human-readable text.

    Args:
        impacts: Detected impacts.

    Returns:
        Formatted Markdown-style bullet list.
    """

    lines = []
    for i in impacts:
        lines.append(f"- [{i.severity.upper()}] {i.symbol}: {i.reason}")
    return "\n".join(lines) if lines else "(no API-impacting changes detected)"


def _run_analyzers(base: str, head: str, cfg: Config) -> List[Impact]:
    """Run enabled analyzer plugins and collect impacts.

    Args:
        base: Base git reference.
        head: Head git reference.
        cfg: Project configuration.

    Returns:
        List of impacts reported by all analyzers.
    """

    impacts: List[Impact] = []
    for analyzer in load_enabled(cfg):
        old = analyzer.collect(base)
        new = analyzer.collect(head)
        impacts.extend(analyzer.compare(old, new))
    return impacts


def _infer_base_ref() -> str:
    """Determine the upstream git reference for the current branch.

    Returns:
        Git reference of the upstream branch. Falls back to ``origin/HEAD`` if
        no upstream is configured.
    """

    import subprocess

    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return "origin/HEAD"


def _commit_tag(pyproject: str, version: str, commit: bool, tag: bool) -> None:
    """Optionally commit and tag the updated version.

    Args:
        pyproject: Path to the ``pyproject.toml`` file.
        version: New version string applied.
        commit: Whether to create a git commit.
        tag: Whether to create a git tag.
    """

    if not (commit or tag):
        return

    import subprocess

    if commit:
        subprocess.run(["git", "add", pyproject], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"chore(release): {version}"], check=True
        )
    if tag:
        subprocess.run(["git", "tag", f"v{version}"], check=True)


def _resolve_pyproject(path: str) -> Path:
    """Locate ``pyproject.toml`` relative to ``path``.

    Args:
        path: User-supplied path to ``pyproject.toml``.

    Returns:
        Resolved path to ``pyproject.toml``.

    Raises:
        FileNotFoundError: If no ``pyproject.toml`` can be found.
    """

    candidate = Path(path)
    if candidate.is_file():
        return candidate
    if candidate.name == "pyproject.toml":
        found = find_pyproject()
        if found:
            return found
    raise FileNotFoundError(f"pyproject.toml not found at {path}")


def decide_command(args: argparse.Namespace) -> int:
    """CLI command to suggest a version bump between two refs.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.
    """

    cfg = load_config(args.config)
    old_api = _build_api_at_ref(args.base, cfg.project.public_roots, cfg.ignore.paths)
    new_api = _build_api_at_ref(args.head, cfg.project.public_roots, cfg.ignore.paths)

    impacts = diff_public_api(
        old_api, new_api, return_type_change=cfg.rules.return_type_change
    )
    impacts.extend(_run_analyzers(args.base, args.head, cfg))
    level = decide_bump(impacts)

    if args.format == "json":
        print(
            json.dumps(
                {"level": level, "impacts": [i.__dict__ for i in impacts]}, indent=2
            )
        )
    elif args.format == "md":
        print(f"**semverbump** suggests: `{level}`\n")
        print(_format_impacts_text(impacts))
    else:
        print(f"Suggested bump: {level}")
        print(_format_impacts_text(impacts))
    return 0


def bump_command(args: argparse.Namespace) -> int:
    """CLI command to apply a version bump.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.
    """

    cfg = load_config(args.config)
    # If level not provided, compute from base/head
    level = args.level
    base = args.base or _infer_base_ref()
    head = args.head
    if not level:
        old_api = _build_api_at_ref(base, cfg.project.public_roots, cfg.ignore.paths)
        new_api = _build_api_at_ref(head, cfg.project.public_roots, cfg.ignore.paths)
        impacts = diff_public_api(
            old_api, new_api, return_type_change=cfg.rules.return_type_change
        )
        impacts.extend(_run_analyzers(base, head, cfg))
        level = decide_bump(impacts)

    try:
        pyproject = _resolve_pyproject(args.pyproject)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    paths = args.version_path or cfg.version.paths
    ignore = args.version_ignore or cfg.version.ignore
    vc = apply_bump(
        level,
        pyproject_path=pyproject,
        dry_run=args.dry_run,
        paths=paths,
        ignore=ignore,
    )
    print(f"Bumped version: {vc.old} -> {vc.new} ({vc.level})")
    if not args.dry_run:
        _commit_tag(str(pyproject), vc.new, args.commit, args.tag)
    return 0


def auto_command(args: argparse.Namespace) -> int:
    """CLI command to decide and apply a version bump in one step.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.
    """

    base = args.base or _infer_base_ref()
    head = args.head
    cfg = load_config(args.config)
    old_api = _build_api_at_ref(base, cfg.project.public_roots, cfg.ignore.paths)
    new_api = _build_api_at_ref(head, cfg.project.public_roots, cfg.ignore.paths)
    impacts = diff_public_api(
        old_api, new_api, return_type_change=cfg.rules.return_type_change
    )
    impacts.extend(_run_analyzers(base, head, cfg))
    level = decide_bump(impacts)
    try:
        pyproject = _resolve_pyproject(args.pyproject)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    paths = args.version_path or cfg.version.paths
    ignore = args.version_ignore or cfg.version.ignore
    vc = apply_bump(
        level,
        pyproject_path=pyproject,
        dry_run=args.dry_run,
        paths=paths,
        ignore=ignore,
    )

    if args.format == "json":
        print(
            json.dumps(
                {
                    "level": level,
                    "impacts": [i.__dict__ for i in impacts],
                    "old_version": vc.old,
                    "new_version": vc.new,
                },
                indent=2,
            )
        )
    elif args.format == "md":
        print(f"**semverbump** suggests: `{level}`\n")
        print(_format_impacts_text(impacts))
        print()
        print(f"Bumped version: {vc.old} -> {vc.new} ({vc.level})")
    else:
        print(f"Suggested bump: {level}")
        print(_format_impacts_text(impacts))
        print(f"Bumped version: {vc.old} -> {vc.new} ({vc.level})")

    if not args.dry_run:
        _commit_tag(str(pyproject), vc.new, args.commit, args.tag)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``semverbump`` CLI.

    Args:
        argv: Optional argument vector.

    Returns:
        Process exit code.
    """

    avail = ", ".join(available()) or "none"
    parser = argparse.ArgumentParser(
        prog="semverbump",
        description=f"Suggest and apply semantic version bumps. Available analyzers: {avail}.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default="semverbump.toml",
        help="Path to configuration file.",
    )

    sub = parser.add_subparsers(dest="cmd")

    p_decide = sub.add_parser(
        "decide",
        help="Suggest bump between two refs",
        description="Compare two git references and report the required semantic version bump.",
    )
    p_decide.add_argument(
        "--base",
        required=True,
        help="Base git reference to compare against (for example 'origin/main').",
    )
    p_decide.add_argument(
        "--head",
        default="HEAD",
        help="Head git reference; defaults to the current HEAD.",
    )
    p_decide.add_argument(
        "--format",
        choices=["text", "md", "json"],
        default="text",
        help="Output style: plain text, Markdown, or machine-readable JSON.",
    )
    p_decide.set_defaults(func=decide_command)

    p_bump = sub.add_parser(
        "bump",
        help="Apply a bump to pyproject.toml",
        description="Update project version metadata and optionally commit and tag the change.",
    )
    p_bump.add_argument(
        "--level",
        choices=["major", "minor", "patch"],
        help="Desired bump level; if omitted, it is inferred from --base and --head.",
    )
    p_bump.add_argument(
        "--base",
        help="Base git reference when auto-deciding the level (uses upstream of HEAD by default).",
    )
    p_bump.add_argument(
        "--head",
        default="HEAD",
        help="Head git reference; defaults to the current HEAD.",
    )
    p_bump.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to the project's pyproject.toml file.",
    )
    p_bump.add_argument(
        "--version-path",
        action="append",
        dest="version_path",
        help="Glob pattern for files that contain the project version (repeatable).",
    )
    p_bump.add_argument(
        "--version-ignore",
        action="append",
        dest="version_ignore",
        help="Glob pattern for paths to exclude from version updates.",
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
    p_bump.set_defaults(func=bump_command)

    p_auto = sub.add_parser(
        "auto",
        help="Decide and apply bump, committing and tagging optionally",
        description=(
            "Combine 'decide' and 'bump' to infer the level and update files in one step."
        ),
    )
    p_auto.add_argument(
        "--base",
        help="Base git reference; defaults to the upstream of the current branch.",
    )
    p_auto.add_argument(
        "--head",
        default="HEAD",
        help="Head git reference; defaults to the current HEAD.",
    )
    p_auto.add_argument(
        "--format",
        choices=["text", "md", "json"],
        default="text",
        help="Output style: plain text, Markdown, or machine-readable JSON.",
    )
    p_auto.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to the project's pyproject.toml file.",
    )
    p_auto.add_argument(
        "--version-path",
        action="append",
        dest="version_path",
        help="Glob pattern for files that contain the project version (repeatable).",
    )
    p_auto.add_argument(
        "--version-ignore",
        action="append",
        dest="version_ignore",
        help="Glob pattern for paths to exclude from version updates.",
    )
    p_auto.add_argument(
        "--commit",
        action="store_true",
        help="Create a git commit for the version change.",
    )
    p_auto.add_argument(
        "--tag", action="store_true", help="Create a git tag for the new version."
    )
    p_auto.add_argument(
        "--dry-run",
        action="store_true",
        help="Display the new version without modifying any files.",
    )
    p_auto.set_defaults(func=auto_command)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
