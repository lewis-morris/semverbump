from __future__ import annotations

import argparse
import json
import sys
from typing import List

from .analyzers import REGISTRY as ANALYZERS
from .compare import Impact, decide_bump, diff_public_api
from .config import Config, load_config
from .gitutils import list_py_files_at_ref, read_file_at_ref
from .public_api import PublicAPI, extract_public_api_from_source, module_name_from_path
from .versioning import apply_bump


def _build_api_at_ref(ref: str, roots: list[str]) -> PublicAPI:
    api: PublicAPI = {}
    # Parse all .py files under roots at this ref
    for root in roots:
        for path in sorted(list_py_files_at_ref(ref, [root])):
            code = read_file_at_ref(ref, path)
            if code is None:
                continue
            modname = module_name_from_path(root, path)
            api.update(extract_public_api_from_source(modname, code))
    return api


def _format_impacts_text(impacts) -> str:
    lines = []
    for i in impacts:
        lines.append(f"- [{i.severity.upper()}] {i.symbol}: {i.reason}")
    return "\n".join(lines) if lines else "(no API-impacting changes detected)"


def _run_analyzers(base: str, head: str, cfg: Config) -> List[Impact]:
    """Run enabled analyzer plugins."""

    impacts: List[Impact] = []
    for name in cfg.analyzers.enabled:
        func = ANALYZERS.get(name)
        if func:
            impacts.extend(func(base, head, cfg))
    return impacts


def decide_cmd(args) -> int:
    cfg = load_config(args.config)
    old_api = _build_api_at_ref(args.base, cfg.project.public_roots)
    new_api = _build_api_at_ref(args.head, cfg.project.public_roots)

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


def bump_cmd(args) -> int:
    # If level not provided, compute from base/head
    level = args.level
    if not level:
        cfg = load_config(args.config)
        old_api = _build_api_at_ref(args.base, cfg.project.public_roots)
        new_api = _build_api_at_ref(args.head, cfg.project.public_roots)
        impacts = diff_public_api(
            old_api, new_api, return_type_change=cfg.rules.return_type_change
        )
        impacts.extend(_run_analyzers(args.base, args.head, cfg))
        level = decide_bump(impacts)

    vc = apply_bump(level, pyproject_path=args.pyproject)
    print(f"Bumped version: {vc.old} -> {vc.new} ({vc.level})")
    if args.commit or args.tag:
        import subprocess

        # Commit
        if args.commit:
            subprocess.run(["git", "add", args.pyproject], check=True)
            subprocess.run(
                ["git", "commit", "-m", f"chore(release): {vc.new}"], check=True
            )
        # Tag
        if args.tag:
            subprocess.run(["git", "tag", f"v{vc.new}"], check=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="semverbump", description="Suggest and apply semantic version bumps."
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
    p_decide.set_defaults(func=decide_cmd)

    p_bump = sub.add_parser("bump", help="Apply a bump to pyproject.toml")
    p_bump.add_argument(
        "--level",
        choices=["major", "minor", "patch"],
        help="Bump level; if omitted, auto-decide from refs",
    )
    p_bump.add_argument("--base", help="Base ref (for auto decide)")
    p_bump.add_argument("--head", default="HEAD", help="Head ref (for auto decide)")
    p_bump.add_argument("--pyproject", default="pyproject.toml")
    p_bump.add_argument(
        "--commit", action="store_true", help="git commit the version change"
    )
    p_bump.add_argument("--tag", action="store_true", help="git tag the new version")
    p_bump.set_defaults(func=bump_cmd)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
