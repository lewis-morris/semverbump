"""Decision helpers for the bumpwright CLI."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from collections.abc import Iterable

from ..analysers import get_analyser_info
from ..analysers.utils import parse_python_source
from ..compare import Decision, Impact, decide_bump, diff_public_api
from ..config import Config
from ..gitutils import last_release_commit, list_py_files_at_ref
from ..public_api import (
    PublicAPI,
    extract_public_api_from_source,
    module_name_from_path,
)
from . import add_analyser_toggles, add_ref_options

logger = logging.getLogger(__name__)


def _build_api_at_ref(
    ref: str,
    roots: list[str],
    ignores: Iterable[str],
    private_prefixes: Iterable[str],
) -> PublicAPI:
    """Collect the public API for ``roots`` at a git reference."""

    api: PublicAPI = {}
    for root in roots:
        paths = sorted(list_py_files_at_ref(ref, [root], ignore_globs=ignores))
        for path in paths:
            tree = parse_python_source(ref, path)
            if tree is None:
                continue
            modname = module_name_from_path(root, path)
            api.update(extract_public_api_from_source(modname, tree, private_prefixes))
    return api


def _format_impacts_text(impacts: list[Impact]) -> str:
    """Render a list of impacts as human-readable text."""

    lines = []
    for i in impacts:
        lines.append(f"- [{i.severity.upper()}] {i.symbol}: {i.reason}")
    return "\n".join(lines) if lines else "(no API-impacting changes detected)"


def add_decide_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared decision-related CLI options to ``parser``.

    Args:
        parser: The parser to extend with ref and analyser options.
    """

    add_ref_options(parser)
    parser.add_argument(
        "--format",
        choices=["text", "md", "json"],
        default="text",
        help="Output style: plain text, Markdown, or machine-readable JSON.",
    )
    add_analyser_toggles(parser)


def _run_analysers(
    base: str,
    head: str,
    cfg: Config,
    enable: Iterable[str] | None = None,
    disable: Iterable[str] | None = None,
) -> list[Impact]:
    """Run analyser plugins and collect impacts."""

    names = set(cfg.analysers.enabled)
    if enable:
        names.update(enable)
    if disable:
        names.difference_update(disable)

    impacts: list[Impact] = []
    for name in names:
        info = get_analyser_info(name)
        if info is None:
            logger.warning("Analyser '%s' is not registered", name)
            continue
        analyser = info.cls(cfg)
        old = analyser.collect(base)
        new = analyser.collect(head)
        impacts.extend(analyser.compare(old, new))
    return impacts


def _infer_base_ref() -> str:
    """Determine the upstream git reference for the current branch."""

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


def _decide_only(args: argparse.Namespace, cfg: Config) -> int:
    """Handle ``bump --decide`` mode."""

    base = args.base or last_release_commit() or "HEAD^"
    head = args.head
    old_api = _build_api_at_ref(
        base,
        cfg.project.public_roots,
        cfg.ignore.paths,
        cfg.project.private_prefixes,
    )
    new_api = _build_api_at_ref(
        head,
        cfg.project.public_roots,
        cfg.ignore.paths,
        cfg.project.private_prefixes,
    )
    impacts = diff_public_api(
        old_api, new_api, return_type_change=cfg.rules.return_type_change
    )
    impacts.extend(
        _run_analysers(base, head, cfg, args.enable_analyser, args.disable_analyser)
    )
    decision = decide_bump(impacts)
    if args.format == "json":
        logger.info(
            json.dumps(
                {
                    "level": decision.level,
                    "confidence": decision.confidence,
                    "reasons": decision.reasons,
                    "impacts": [i.__dict__ for i in impacts],
                },
                indent=2,
            )
        )
    elif args.format == "md":
        logger.info("**bumpwright** suggests: `%s`\n", decision.level)
        logger.info("%s", _format_impacts_text(impacts))
    else:
        logger.info("Suggested bump: %s", decision.level)
        logger.info("%s", _format_impacts_text(impacts))
    return 0


def _infer_level(
    base: str,
    head: str,
    cfg: Config,
    args: argparse.Namespace,
) -> Decision:
    """Compute bump level from repository differences."""

    old_api = _build_api_at_ref(
        base,
        cfg.project.public_roots,
        cfg.ignore.paths,
        cfg.project.private_prefixes,
    )
    new_api = _build_api_at_ref(
        head,
        cfg.project.public_roots,
        cfg.ignore.paths,
        cfg.project.private_prefixes,
    )
    impacts = diff_public_api(
        old_api, new_api, return_type_change=cfg.rules.return_type_change
    )
    impacts.extend(
        _run_analysers(base, head, cfg, args.enable_analyser, args.disable_analyser)
    )
    return decide_bump(impacts)
