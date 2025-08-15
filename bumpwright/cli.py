"""Command-line interface for the :mod:`bumpwright` project.

This module exposes subcommands for suggesting and applying semantic version
bumps based on public API differences and additional analyzers.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Iterable, List

from .analyzers import available, load_enabled
from .compare import Impact, decide_bump, diff_public_api
from .config import Config, load_config
from .gitutils import (
    changed_paths,
    collect_commits,
    last_release_commit,
    list_py_files_at_ref,
    read_file_at_ref,
)
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

    Examples:
        Build the API for the current ``HEAD`` for modules under ``src``:

        >>> _build_api_at_ref("HEAD", ["src"], [])
        {'pkg.module.func': '() -> None', ...}
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

    Examples:
        >>> _format_impacts_text([])
        '(no API-impacting changes detected)'
        >>> _format_impacts_text([Impact('warn', 'sym', 'reason')])
        '- [WARN] sym: reason'
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

    Examples:
        >>> cfg = load_config("bumpwright.toml")
        >>> _run_analyzers("HEAD^", "HEAD", cfg)
        [Impact(...), ...]
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

    Examples:
        >>> _infer_base_ref()
        'origin/main'
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

    Examples:
        Create a commit only:

        >>> _commit_tag("pyproject.toml", "1.2.3", commit=True, tag=False)
        # commits "chore(release): 1.2.3"
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

    Examples:
        >>> _resolve_pyproject("pyproject.toml")  # doctest: +SKIP
        PosixPath('pyproject.toml')
    """

    candidate = Path(path)
    if candidate.is_file():
        return candidate
    if candidate.name == "pyproject.toml":
        found = find_pyproject()
        if found:
            return found
    raise FileNotFoundError(f"pyproject.toml not found at {path}")


def init_command(args: argparse.Namespace) -> int:
    """CLI command to create an empty baseline release commit.

    This command records an empty ``chore(release): initialize baseline`` commit
    so that subsequent invocations of :func:`last_release_commit` have a
    reference point. It is typically run once when integrating bumpwright into a
    project that lacks prior release commits.

    Args:
        args: Parsed command-line arguments (unused).

    Returns:
        Process exit code.

    Examples:
        >>> init_command(argparse.Namespace())  # doctest: +SKIP
        0
    """

    if last_release_commit() is not None:
        print("Baseline already initialized.")
        return 0

    import subprocess

    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "chore(release): initialize baseline",
        ],
        check=True,
    )
    print("Created baseline release commit.")
    return 0


def decide_command(args: argparse.Namespace) -> int:
    """CLI command to suggest a version bump between two refs.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.

    Examples:
        Compare the current commit to its parent (default ``--base`` is the last
        release commit or ``HEAD^``) and display Markdown output:

        $ bumpwright decide --format md
        **bumpwright** suggests: `patch`

        (no API-impacting changes detected)

        Emit machine-readable JSON instead:

        $ bumpwright decide --format json
        {
          "level": "patch",
          "impacts": []
        }
    """

    cfg = load_config(args.config)
    # Default to comparing the current commit against the latest release when no
    # explicit base is provided.
    if args.base:
        base: str = args.base
    else:
        base = last_release_commit() or "HEAD^"
    head: str = args.head
    old_api = _build_api_at_ref(base, cfg.project.public_roots, cfg.ignore.paths)
    new_api = _build_api_at_ref(head, cfg.project.public_roots, cfg.ignore.paths)

    impacts = diff_public_api(
        old_api, new_api, return_type_change=cfg.rules.return_type_change
    )
    impacts.extend(_run_analyzers(base, head, cfg))
    level = decide_bump(impacts)

    if args.format == "json":
        print(
            json.dumps(
                {"level": level, "impacts": [i.__dict__ for i in impacts]}, indent=2
            )
        )
    elif args.format == "md":
        print(f"**bumpwright** suggests: `{level}`\n")
        print(_format_impacts_text(impacts))
    else:
        print(f"Suggested bump: {level}")
        print(_format_impacts_text(impacts))
    return 0


def bump_command(args: argparse.Namespace) -> int:
    """CLI command to apply a version bump.

    If ``--level`` is not specified, the bump level is inferred by comparing
    ``--base`` (defaults to the last release commit or the previous commit
    ``HEAD^``) and ``--head`` (defaults to ``HEAD``).

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.

    Examples:
        Dry-run the inferred bump against the previous commit:

        $ bumpwright bump --dry-run
        Bumped version: 1.2.3 -> 1.2.4 (patch)

        Emit JSON for automation:

        $ bumpwright bump --dry-run --format json
        {
          "old_version": "1.2.3",
          "new_version": "1.2.4",
          "level": "patch"
        }

        Apply an explicit minor bump and create a commit:

        $ bumpwright bump --level minor --commit
        Bumped version: 1.2.3 -> 1.3.0 (minor)

    If no relevant files have changed or no API impacts are detected, the
    command prints ``No version bump needed`` and exits without modifying the
    project version.
    """

    cfg = load_config(args.config)
    # If level not provided, compute from base/head
    level = args.level
    if args.base:
        base = args.base
    elif level:
        base = "HEAD^"
    else:
        base = last_release_commit() or "HEAD^"
    head = args.head

    try:
        pyproject = _resolve_pyproject(args.pyproject)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    paths = args.version_path or cfg.version.paths
    version_files = {p for p in paths if not any(ch in p for ch in "*?[")}

    try:
        changed = changed_paths(base, head)
    except Exception:  # git diff may fail on initial commit
        changed = None

    if changed is not None:
        filtered = {
            p for p in changed if p != Path(pyproject).name and p not in version_files
        }
        if not filtered:
            print("No version bump needed")
            return 0

    if not level:
        old_api = _build_api_at_ref(base, cfg.project.public_roots, cfg.ignore.paths)
        new_api = _build_api_at_ref(head, cfg.project.public_roots, cfg.ignore.paths)
        impacts = diff_public_api(
            old_api, new_api, return_type_change=cfg.rules.return_type_change
        )
        impacts.extend(_run_analyzers(base, head, cfg))
        level = decide_bump(impacts)
        if level is None:
            print("No version bump needed")
            return 0

    ignore = args.version_ignore or cfg.version.ignore
    vc = apply_bump(
        level,
        pyproject_path=pyproject,
        dry_run=args.dry_run,
        paths=paths,
        ignore=ignore,
    )
    changelog: str | None = None
    if args.changelog is not None:
        base = last_release_commit() or f"{args.head}^"
        commits = collect_commits(base, args.head)
        lines = [f"## [v{vc.new}] - {date.today().isoformat()}"]
        lines.extend(f"- {sha} {subject}" for sha, subject in commits)
        changelog = "\n".join(lines) + "\n"
    if args.format == "json":
        print(
            json.dumps(
                {
                    "old_version": vc.old,
                    "new_version": vc.new,
                    "level": vc.level,
                },
                indent=2,
            )
        )
    elif args.format == "md":
        print(f"Bumped version: `{vc.old}` -> `{vc.new}` ({vc.level})")
    else:
        print(f"Bumped version: {vc.old} -> {vc.new} ({vc.level})")
    if not args.dry_run:
        _commit_tag(str(pyproject), vc.new, args.commit, args.tag)
    if changelog is not None:
        if args.changelog == "-":
            print(changelog, end="")
        else:
            with open(args.changelog, "a", encoding="utf-8") as fh:
                fh.write(changelog)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``bumpwright`` CLI.

    Args:
        argv: Optional argument vector.

    Returns:
        Process exit code.
    """

    avail = ", ".join(available()) or "none"
    parser = argparse.ArgumentParser(
        prog="bumpwright",
        description=f"Suggest and apply semantic version bumps. Available analyzers: {avail}.",
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
            "Create an empty 'chore(release): initialize baseline' commit to "
            "establish a comparison point for future bumps."
        ),
    )
    p_init.set_defaults(func=init_command)

    p_decide = sub.add_parser(
        "decide",
        help="Suggest bump between two refs",
        description="Compare two git references and report the required semantic version bump.",
    )
    p_decide.add_argument(
        "--base",
        help=(
            "Base git reference to compare against. Defaults to the last release commit "
            "or the previous commit (HEAD^)."
        ),
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
        help=(
            "Base git reference when auto-deciding the level. Defaults to the last release "
            "commit or the previous commit (HEAD^)."
        ),
    )
    p_bump.add_argument(
        "--head",
        default="HEAD",
        help="Head git reference; defaults to the current HEAD.",
    )
    p_bump.add_argument(
        "--format",
        choices=["text", "md", "json"],
        default="text",
        help="Output style: plain text, Markdown, or machine-readable JSON.",
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
    p_bump.add_argument(
        "--changelog",
        nargs="?",
        const="-",
        help="Append release notes to FILE or stdout when no path is given.",
    )
    p_bump.set_defaults(func=bump_command)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
