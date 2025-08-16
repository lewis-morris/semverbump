"""Version bump command for the bumpwright CLI."""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
from datetime import date
from glob import has_magic
from pathlib import Path
from typing import Any, Iterable

from jinja2 import Template

from ..compare import Decision
from ..config import Config, load_config
from ..gitutils import changed_paths, collect_commits, last_release_commit
from ..versioning import VersionChange, apply_bump, find_pyproject
from .decide import _decide_only, _infer_level

logger = logging.getLogger(__name__)


def get_default_template() -> str:
    """Return the built-in changelog template text.

    The template is loaded lazily to avoid unnecessary disk reads when
    changelog generation is not requested.

    Returns:
        Default changelog template contents.
    """

    template_path = (
        Path(__file__).resolve().parents[1] / "templates" / "changelog.md.j2"
    )
    return template_path.read_text(encoding="utf-8")


def _read_template(template_path: str | None) -> str:
    """Load a changelog template from ``template_path`` or return the default.

    Args:
        template_path: Optional filesystem path to a custom template.

    Returns:
        Template contents as a string.
    """

    if template_path:
        return Path(template_path).read_text(encoding="utf-8")
    return get_default_template()


def _commit_tag(
    files: Iterable[str | Path], version: str, commit: bool, tag: bool
) -> None:
    """Optionally commit and tag the updated version.

    Args:
        files: Paths of files to stage before committing.
        version: Version string to commit and tag.
        commit: Whether to create a commit.
        tag: Whether to create a git tag.

    Raises:
        RuntimeError: If the requested tag already exists.
    """

    if not (commit or tag):
        return

    if tag:
        # Abort early if the tag already exists to avoid accidental reuse.
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"v{version}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            msg = f"Tag v{version} already exists. Delete the tag manually or use a different version."
            raise RuntimeError(msg)

    if commit:
        for file in files:
            subprocess.run(["git", "add", str(file)], check=True)
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
    """Return changed paths, handling missing history gracefully.

    Args:
        base: Base git reference for comparison.
        head: Head git reference for comparison.

    Returns:
        A set of changed paths or ``None`` when the diff cannot be determined.
    """

    try:
        return changed_paths(base, head)
    except subprocess.CalledProcessError:
        logger.warning("Failed to compute changed paths between %s and %s", base, head)
        return None


def _build_changelog(args: argparse.Namespace, new_version: str) -> str | None:
    """Generate changelog text if requested.

    Changelog entries are rendered using a Jinja2 template. Users may supply a
    custom template via ``--changelog-template`` or configuration; otherwise the
    built-in template is used. Commits whose subjects match any pattern from
    ``--changelog-exclude`` or configuration are omitted. Available template
    variables include:

    ``version``
        New project version string.
    ``date``
        Current date in ISO format.
    ``commits``
        Sequence of mappings with ``sha``, ``subject``, and optional ``link``
        keys representing commits since the previous release.
    """

    if args.changelog is None:
        return None
    base = last_release_commit() or f"{args.head}^"
    commits = collect_commits(base, args.head)
    patterns = [re.compile(p) for p in getattr(args, "changelog_exclude", [])]
    entries: list[dict[str, Any]] = []
    for sha, subject in commits:
        if any(p.search(subject) for p in patterns):
            continue
        link = None
        if args.repo_url:
            base_url = args.repo_url.rstrip("/")
            link = f"{base_url}/commit/{sha}"
        entries.append({"sha": sha, "subject": subject, "link": link})
    tmpl = Template(_read_template(getattr(args, "changelog_template", None)))
    rendered = tmpl.render(
        version=new_version,
        date=date.today().isoformat(),
        commits=entries,
        repo_url=args.repo_url,
    )
    return rendered.rstrip() + "\n"


def _prepare_version_files(
    cfg: Config,
    args: argparse.Namespace,
    pyproject: Path,
    base: str,
    head: str,
) -> list[str] | None:
    """Build version file list and decide if a bump is necessary.

    Args:
        cfg: Project configuration object.
        args: Parsed command line arguments.
        pyproject: Path to the canonical ``pyproject.toml`` file.
        base: Git reference representing the comparison base.
        head: Git reference representing the comparison head.

    Returns:
        List of file patterns to update, or ``None`` when no bump is required.
    """

    paths = list(cfg.version.paths)
    if args.version_path:
        paths.extend(args.version_path)
    version_files = {p for p in paths if not has_magic(p)}
    changed = _safe_changed_paths(base, head)
    if changed is not None:
        filtered = {
            p for p in changed if p != pyproject.name and p not in version_files
        }
        if not filtered:
            return None
    return paths


def _display_result(
    args: argparse.Namespace, vc: VersionChange, decision: Decision
) -> None:
    """Show bump outcome using the selected format."""

    if args.format == "json":
        logger.info(
            json.dumps(
                {
                    "old_version": vc.old,
                    "new_version": vc.new,
                    "level": vc.level,
                    "confidence": decision.confidence,
                    "reasons": decision.reasons,
                    "files": [str(p) for p in vc.files],
                    "skipped": [str(p) for p in vc.skipped],
                },
                indent=2,
            )
        )
    elif args.format == "md":
        logger.info("Bumped version: `%s` -> `%s` (%s)", vc.old, vc.new, vc.level)
        logger.info(
            "Updated files:\n%s",
            "\n".join(f"- `{p}`" for p in vc.files),
        )
        if vc.skipped:
            logger.info(
                "Skipped files:\n%s",
                "\n".join(f"- `{p}`" for p in vc.skipped),
            )
    else:
        logger.info("Bumped version: %s -> %s (%s)", vc.old, vc.new, vc.level)
        logger.info("Updated files: %s", ", ".join(str(p) for p in vc.files))
        if vc.skipped:
            logger.info("Skipped files: %s", ", ".join(str(p) for p in vc.skipped))


def _write_changelog(args: argparse.Namespace, changelog: str | None) -> None:
    """Persist changelog content based on user options."""

    if changelog is None:
        return
    if args.changelog == "-":
        logger.info("%s", changelog.rstrip())
    else:
        with open(args.changelog, "a", encoding="utf-8") as fh:
            fh.write(changelog)


def bump_command(args: argparse.Namespace) -> int:
    """Apply a version bump based on repository changes.

    Args:
        args: Parsed command-line arguments with fields corresponding to CLI
            options. Important attributes include:

            config (str): Path to configuration file. Defaults to
                ``bumpwright.toml``.

            level (str | None): Desired bump level (``major``, ``minor``, or
                ``patch``) or ``None`` to infer the level automatically.

            base (str | None): Git reference used as the comparison base when
                inferring the bump level. Defaults to the last release commit or
                ``HEAD^``.

            head (str): Git reference representing the working tree. Defaults to
                ``HEAD``.

            format (str): Output format, one of ``text`` (default), ``md``, or
                ``json``.

            repo_url (str | None): Base repository URL for generating commit
                links in Markdown output.

            decide (bool): When ``True``, only report the bump level without
                modifying any files.

            enable_analyser (list[str]): Names of analysers to enable in
                addition to configuration.

            disable_analyser (list[str]): Names of analysers to disable even if
                configured.

            pyproject (str): Path to ``pyproject.toml``. Defaults to
                ``pyproject.toml``.

            version_path (list[str]): Extra glob patterns for files whose
                version fields should be updated. Defaults include
                ``pyproject.toml``, ``setup.py``, ``setup.cfg``, and any
                ``__init__.py``, ``version.py``, or ``_version.py`` files.

            version_ignore (list[str]): Glob patterns for paths to exclude from
                version updates.

            commit (bool): Create a git commit containing the version change.

            tag (bool): Create a git tag for the new version.

            dry_run (bool): Show the new version without modifying files.

            changelog (str | None): Write release notes to the given file or
                stdout when ``-`` is provided.

            changelog_template (str | None): Path to a Jinja2 template used to
                render changelog entries. Defaults to the built-in template.

            changelog_exclude (list[str]): Regex patterns of commit subjects to
                exclude from changelog entries.

    Returns:
        Exit status code. ``0`` indicates success; ``1`` indicates an error.
    """

    cfg: Config = load_config(args.config)
    if args.changelog is None and cfg.changelog.path:
        args.changelog = cfg.changelog.path
    if getattr(args, "changelog_template", None) is None and cfg.changelog.template:
        args.changelog_template = cfg.changelog.template
    excludes = list(cfg.changelog.exclude)
    cli_excludes = getattr(args, "changelog_exclude", []) or []
    excludes.extend(cli_excludes)
    args.changelog_exclude = excludes
    if args.decide:
        return _decide_only(args, cfg)

    level = args.level
    decision: Decision | None = None
    base, head = _resolve_refs(args, level)

    try:
        pyproject = _resolve_pyproject(args.pyproject)
    except FileNotFoundError as exc:
        logger.error("Error: %s", exc)
        return 1
    paths = _prepare_version_files(cfg, args, pyproject, base, head)
    if paths is None:
        logger.info("No version bump needed")
        return 0

    if not level:
        decision = _infer_level(base, head, cfg, args)
        if decision.level is None:
            logger.info("No version bump needed")
            return 0
        level = decision.level
    else:
        decision = Decision(level, 1.0, [])

    if (args.commit or args.tag) and not args.dry_run:
        status: subprocess.CompletedProcess[str] = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        )
        if status.stdout.strip():
            logger.error("Error: working directory has uncommitted changes")
            return 1

    ignore = list(cfg.version.ignore)
    if args.version_ignore:
        ignore.extend(args.version_ignore)
    vc = apply_bump(
        level,
        pyproject_path=pyproject,
        dry_run=args.dry_run,
        paths=paths,
        ignore=ignore,
        cfg=cfg,
    )
    changelog = _build_changelog(args, vc.new)
    _display_result(args, vc, decision)
    if not args.dry_run:
        _commit_tag(vc.files, vc.new, args.commit, args.tag)
    _write_changelog(args, changelog)
    return 0
