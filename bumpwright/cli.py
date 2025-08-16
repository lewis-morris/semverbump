"""Command-line interface for the :mod:`bumpwright` project.

This module exposes subcommands for suggesting and applying semantic version
bumps based on public API differences and additional analyzers.
"""

from __future__ import annotations

import argparse
import json
import subprocess
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


def _run_analyzers(
    base: str, head: str, cfg: Config, names: Iterable[str] | None = None
) -> List[Impact]:
    """Run selected analyzer plugins and collect impacts.

    Args:
        base: Base git reference.
        head: Head git reference.
        cfg: Project configuration.
        names: Optional collection of analyzer names to execute. When ``None``,
            analyzers enabled in ``cfg`` are used.

    Returns:
        List of impacts reported by all analyzers.

    Examples:
        >>> cfg = load_config("bumpwright.toml")
        >>> _run_analyzers("HEAD^", "HEAD", cfg)
        [Impact(...), ...]
    """

    impacts: List[Impact] = []
    for analyzer in load_enabled(cfg, names):
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


def init_command(_args: argparse.Namespace) -> int:
    """Create an empty baseline release commit.

    This command records an empty ``chore(release): initialize baseline`` commit
    so that subsequent invocations of :func:`last_release_commit` have a
    reference point. It is typically run once when integrating bumpwright into a
    project that lacks prior release commits.

    Args:
        _args: Parsed command-line arguments (unused).

    Returns:
        Process exit code.

    Examples:
        >>> init_command(argparse.Namespace())  # doctest: +SKIP
        0
    """

    if last_release_commit() is not None:
        print("Baseline already initialized.")
        return 0

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


def _decide_only(args: argparse.Namespace, cfg: Config) -> int:
    """Handle ``bump --decide`` mode.

    Args:
        args: Parsed command-line arguments.
        cfg: Project configuration settings.

    Returns:
        Process exit code.
    """

    base = args.base or last_release_commit() or "HEAD^"
    head = args.head
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
                {"level": level, "impacts": [i.__dict__ for i in impacts]},
                indent=2,
            )
        )
    elif args.format == "md":
        print(f"**bumpwright** suggests: `{level}`\n")
        print(_format_impacts_text(impacts))
    else:
        print(f"Suggested bump: {level}")
        print(_format_impacts_text(impacts))
    return 0


def _resolve_refs(args: argparse.Namespace, level: str | None) -> tuple[str, str]:
    """Determine base and head git references.

    Args:
        args: Parsed command-line arguments.
        level: Desired bump level if already known.

    Returns:
        Tuple of ``(base, head)`` references.
    """

    if args.base:
        base = args.base
    elif level:
        base = "HEAD^"
    else:
        base = last_release_commit() or "HEAD^"
    return base, args.head


def _safe_changed_paths(base: str, head: str) -> set[str] | None:
    """Return changed paths, handling missing history gracefully.

    Args:
        base: Older git reference.
        head: Newer git reference.

    Returns:
        Set of changed file paths or ``None`` if history lookup fails.
    """

    try:
        return changed_paths(base, head)
    except subprocess.CalledProcessError:
        return None


def _infer_level(base: str, head: str, cfg: Config) -> str | None:
    """Compute bump level from repository differences.

    Args:
        base: Base git reference.
        head: Head git reference.
        cfg: Project configuration settings.

    Returns:
        Suggested bump level or ``None`` if no change is required.
    """

    old_api = _build_api_at_ref(base, cfg.project.public_roots, cfg.ignore.paths)
    new_api = _build_api_at_ref(head, cfg.project.public_roots, cfg.ignore.paths)
    impacts = diff_public_api(
        old_api, new_api, return_type_change=cfg.rules.return_type_change
    )
    impacts.extend(_run_analyzers(base, head, cfg))
    return decide_bump(impacts)


def _build_changelog(args: argparse.Namespace, new_version: str) -> str | None:
    """Generate changelog text if requested.

    Args:
        args: Parsed command-line arguments.
        new_version: Newly computed project version.

    Returns:
        Rendered changelog text or ``None`` when changelog generation is disabled.
    """

    if args.changelog is None:
        return None
    base = last_release_commit() or f"{args.head}^"
    commits = collect_commits(base, args.head)
    lines = [f"## [v{new_version}] - {date.today().isoformat()}"]
    for sha, subject in commits:
        if args.repo_url and args.format == "md":
            base_url = args.repo_url.rstrip("/")
            link = f"{base_url}/commit/{sha}"
            lines.append(f"- [{sha}]({link}) {subject}")
        else:
            lines.append(f"- {sha} {subject}")
    return "\n".join(lines) + "\n"


def bump_command(args: argparse.Namespace) -> int:
    """Apply a version bump based on repository changes.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.
    """

    cfg = load_config(
        args.config,
        enable=args.enable_analyzer,
        disable=args.disable_analyzer,
    )
    if args.decide:
        return _decide_only(args, cfg)

    level = args.level
    base, head = _resolve_refs(args, level)

    try:
        pyproject = _resolve_pyproject(args.pyproject)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    paths = list(cfg.version.paths)
    if args.version_path:
        paths.extend(args.version_path)
    version_files = {p for p in paths if not any(ch in p for ch in "*?[")}
    changed = _safe_changed_paths(base, head)
    if changed is not None:
        filtered = {
            p for p in changed if p != Path(pyproject).name and p not in version_files
        }
        if not filtered:
            print("No version bump needed")
            return 0

    if not level:
        level = _infer_level(base, head, cfg)
        if level is None:
            print("No version bump needed")
            return 0

    ignore = list(cfg.version.ignore)
    if args.version_ignore:
        ignore.extend(args.version_ignore)
    vc = apply_bump(
        level,
        pyproject_path=pyproject,
        dry_run=args.dry_run,
        paths=paths,
        ignore=ignore,
    )
    changelog = _build_changelog(args, vc.new)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "old_version": vc.old,
                    "new_version": vc.new,
                    "level": vc.level,
                    "files": [str(p) for p in vc.files],
                },
                indent=2,
            )
        )
    elif args.format == "md":
        print(f"Bumped version: `{vc.old}` -> `{vc.new}` ({vc.level})")
        print("Updated files:\n" + "\n".join(f"- `{p}`" for p in vc.files))
    else:
        print(f"Bumped version: {vc.old} -> {vc.new} ({vc.level})")
        print("Updated files: " + ", ".join(str(p) for p in vc.files))
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
        "--repo-url",
        help="Base repository URL for linking commit hashes in Markdown output.",
    )
    p_bump.add_argument(
        "--decide",
        action="store_true",
        help="Only determine the bump level without modifying any files.",
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
        help=(
            "Glob pattern for paths to exclude from version updates " "(repeatable)."
        ),
    )
    p_bump.add_argument(
        "--enable-analyzer",
        action="append",
        dest="enable_analyzer",
        help="Enable analyzer NAME for this run (repeatable).",
    )
    p_bump.add_argument(
        "--disable-analyzer",
        action="append",
        dest="disable_analyzer",
        help="Disable analyzer NAME for this run (repeatable).",
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
