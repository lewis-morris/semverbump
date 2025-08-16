"""Version bump command for the bumpwright CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from ..compare import Decision
from ..config import Config, load_config
from ..gitutils import changed_paths, collect_commits, last_release_commit
from ..versioning import apply_bump, find_pyproject
from .decide import _decide_only, _infer_level


def _commit_tag(pyproject: str, version: str, commit: bool, tag: bool) -> None:
    """Optionally commit and tag the updated version."""

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
    """Locate ``pyproject.toml`` relative to ``path``."""

    candidate = Path(path)
    if candidate.is_file():
        return candidate
    if candidate.name == "pyproject.toml":
        found = find_pyproject()
        if found:
            return found
    raise FileNotFoundError(f"pyproject.toml not found at {path}")


def _resolve_refs(args: argparse.Namespace, level: str | None) -> tuple[str, str]:
    """Determine base and head git references."""

    if args.base:
        base = args.base
    elif level:
        base = "HEAD^"
    else:
        base = last_release_commit() or "HEAD^"
    return base, args.head


def _safe_changed_paths(base: str, head: str) -> set[str] | None:
    """Return changed paths, handling missing history gracefully."""

    try:
        return changed_paths(base, head)
    except subprocess.CalledProcessError:
        return None


def _build_changelog(args: argparse.Namespace, new_version: str) -> str | None:
    """Generate changelog text if requested."""

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
    """Apply a version bump based on repository changes."""

    cfg: Config = load_config(args.config)
    if args.changelog is None and cfg.changelog.path:
        args.changelog = cfg.changelog.path
    if args.decide:
        return _decide_only(args, cfg)

    level = args.level
    decision: Decision | None = None
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
        decision = _infer_level(base, head, cfg, args)
        if decision.level is None:
            print("No version bump needed")
            return 0
        level = decision.level
    else:
        decision = Decision(level, 1.0, [])

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
                    "confidence": decision.confidence,
                    "reasons": decision.reasons,
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
