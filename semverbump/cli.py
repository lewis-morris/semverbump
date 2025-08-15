"""Command-line interface for the :mod:`semverbump` project.

This module exposes subcommands for suggesting and applying semantic version
bumps based on public API differences and additional analyzers.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable, List

from .analyzers import available, load_enabled
from .compare import Impact, decide_bump, diff_public_api
from .config import Config, load_config
from .gitutils import list_py_files_at_ref, read_file_at_ref
from .public_api import PublicAPI, extract_public_api_from_source, module_name_from_path
from .versioning import apply_bump


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

    vc = apply_bump(
        level,
        pyproject_path=args.pyproject,
        source=cfg.project.version_source,
    )
    print(f"Bumped version: {vc.old} -> {vc.new} ({vc.level})")
    _commit_tag(args.pyproject, vc.new, args.commit, args.tag)
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
    vc = apply_bump(
        level,
        pyproject_path=args.pyproject,
        source=cfg.project.version_source,
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

    _commit_tag(args.pyproject, vc.new, args.commit, args.tag)
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
        description=(
            f"Suggest and apply semantic version bumps. Available analyzers: {avail}.",
        ),
    )
    parser.add_argument(
        "--config",
        default="semverbump.toml",
        help="Path to config (default: semverbump.toml)",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_decide = sub.add_parser("decide", help="Suggest bump between two refs")
    p_decide.add_argument(
        "--base", required=True, help="Base ref (e.g., origin/master)"
    )
    p_decide.add_argument("--head", default="HEAD", help="Head ref (default: HEAD)")
    p_decide.add_argument("--format", choices=["text", "md", "json"], default="text")
    p_decide.set_defaults(func=decide_command)

    p_bump = sub.add_parser("bump", help="Apply a bump to pyproject.toml")
    p_bump.add_argument(
        "--level",
        choices=["major", "minor", "patch"],
        help="Bump level; if omitted, auto-decide from refs",
    )
    p_bump.add_argument(
        "--base",
        help="Base ref (defaults to upstream of HEAD when --level omitted)",
    )
    p_bump.add_argument("--head", default="HEAD", help="Head ref (default: HEAD)")
    p_bump.add_argument("--pyproject", default="pyproject.toml")
    p_bump.add_argument(
        "--commit",
        action="store_true",
        help="git commit the version change",
    )
    p_bump.add_argument("--tag", action="store_true", help="git tag the new version")
    p_bump.set_defaults(func=bump_command)

    p_auto = sub.add_parser(
        "auto", help="Decide and apply bump, committing and tagging optionally"
    )
    p_auto.add_argument(
        "--base",
        help="Base ref (defaults to upstream of HEAD)",
    )
    p_auto.add_argument("--head", default="HEAD", help="Head ref (default: HEAD)")
    p_auto.add_argument("--format", choices=["text", "md", "json"], default="text")
    p_auto.add_argument("--pyproject", default="pyproject.toml")
    p_auto.add_argument(
        "--commit",
        action="store_true",
        help="git commit the version change",
    )
    p_auto.add_argument("--tag", action="store_true", help="git tag the new version")
    p_auto.set_defaults(func=auto_command)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
