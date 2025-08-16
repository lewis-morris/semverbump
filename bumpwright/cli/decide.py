"""Decision helpers for the bumpwright CLI."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from collections.abc import Iterable

from ..analyzers import get_analyzer_info
from ..analyzers.utils import iter_py_files_at_ref
from ..compare import Decision, Impact, decide_bump, diff_public_api
from ..config import Config
from ..gitutils import last_release_commit
from ..public_api import (
    PublicAPI,
    extract_public_api_from_source,
    module_name_from_path,
)

logger = logging.getLogger(__name__)


def _build_api_at_ref(ref: str, roots: list[str], ignores: Iterable[str]) -> PublicAPI:
    """Collect the public API for ``roots`` at a git reference."""

    api: PublicAPI = {}
    for root in roots:
        for path, code in sorted(
            iter_py_files_at_ref(ref, [root], ignores), key=lambda t: t[0]
        ):
            modname = module_name_from_path(root, path)
            api.update(extract_public_api_from_source(modname, code))
    return api


def _format_impacts_text(impacts: list[Impact]) -> str:
    """Render a list of impacts as human-readable text."""

    lines = []
    for i in impacts:
        lines.append(f"- [{i.severity.upper()}] {i.symbol}: {i.reason}")
    return "\n".join(lines) if lines else "(no API-impacting changes detected)"


def _run_analyzers(
    base: str,
    head: str,
    cfg: Config,
    enable: Iterable[str] | None = None,
    disable: Iterable[str] | None = None,
) -> list[Impact]:
    """Run analyzer plugins and collect impacts."""

    names = set(cfg.analyzers.enabled)
    if enable:
        names.update(enable)
    if disable:
        names.difference_update(disable)

    impacts: list[Impact] = []
    for name in names:
        info = get_analyzer_info(name)
        if info is None:
            logger.warning("Analyzer '%s' is not registered", name)
            continue
        analyzer = info.cls(cfg)
        old = analyzer.collect(base)
        new = analyzer.collect(head)
        impacts.extend(analyzer.compare(old, new))
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
    old_api = _build_api_at_ref(base, cfg.project.public_roots, cfg.ignore.paths)
    new_api = _build_api_at_ref(head, cfg.project.public_roots, cfg.ignore.paths)
    impacts = diff_public_api(
        old_api, new_api, return_type_change=cfg.rules.return_type_change
    )
    impacts.extend(
        _run_analyzers(base, head, cfg, args.enable_analyzer, args.disable_analyzer)
    )
    decision = decide_bump(impacts)
    if args.format == "json":
        print(
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
        print(f"**bumpwright** suggests: `{decision.level}`\n")
        print(_format_impacts_text(impacts))
    else:
        print(f"Suggested bump: {decision.level}")
        print(_format_impacts_text(impacts))
    return 0


def _infer_level(
    base: str,
    head: str,
    cfg: Config,
    args: argparse.Namespace,
) -> Decision:
    """Compute bump level from repository differences."""

    old_api = _build_api_at_ref(base, cfg.project.public_roots, cfg.ignore.paths)
    new_api = _build_api_at_ref(head, cfg.project.public_roots, cfg.ignore.paths)
    impacts = diff_public_api(
        old_api, new_api, return_type_change=cfg.rules.return_type_change
    )
    impacts.extend(
        _run_analyzers(base, head, cfg, args.enable_analyzer, args.disable_analyzer)
    )
    return decide_bump(impacts)
