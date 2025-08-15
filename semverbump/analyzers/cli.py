"""CLI analyzer for detecting interface changes.

This module introspects ``argparse`` and ``click`` command definitions to
produce a simple representation of a command line interface. The resulting
representation can be diffed between two versions to determine the semantic
version impact of CLI changes.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Dict, List

from ..compare import Impact
from ..gitutils import read_file_at_ref

try:
    import click  # type: ignore
except Exception:  # pragma: no cover - click optional
    click = None  # type: ignore


@dataclass
class CommandSpec:
    """Description of a single command.

    Attributes:
        options: Mapping of option/argument name to a boolean indicating
            whether it is required.
    """

    options: Dict[str, bool]


CLI = Dict[str, CommandSpec]


def _extract_argparse(parser: argparse.ArgumentParser, prefix: str = "") -> CLI:
    """Extract command specifications from an ``argparse`` parser.

    Args:
        parser: Parser to inspect.
        prefix: Command path accumulated during recursion.

    Returns:
        Mapping of command paths to their specifications.
    """

    result: CLI = {}
    opts: Dict[str, bool] = {}
    for action in parser._actions:  # type: ignore[attr-defined]
        if isinstance(action, argparse._SubParsersAction):  # type: ignore[attr-defined]
            for name, sub in action.choices.items():
                new_prefix = f"{prefix} {name}".strip()
                result.update(_extract_argparse(sub, new_prefix))
        else:
            if action.dest == "help":
                continue
            required = getattr(action, "required", False)
            if not action.option_strings:
                required = True
            opts[action.dest] = required
    result[prefix] = CommandSpec(opts)
    return result


def _extract_click(cmd: "click.core.Command", prefix: str = "") -> CLI:  # type: ignore
    """Extract command specifications from a ``click`` command object.

    Args:
        cmd: Click command or group to inspect.
        prefix: Command path accumulated during recursion.

    Returns:
        Mapping of command paths to their specifications.
    """

    result: CLI = {}
    opts = {p.name: p.required for p in getattr(cmd, "params", [])}
    result[prefix] = CommandSpec(opts)
    if isinstance(cmd, getattr(click, "Group", tuple())):
        for name, sub in cmd.commands.items():
            new_prefix = f"{prefix} {name}".strip()
            result.update(_extract_click(sub, new_prefix))
    return result


def extract_cli(obj: Any) -> CLI:
    """Create a CLI specification from ``argparse`` or ``click`` objects.

    Args:
        obj: ``argparse.ArgumentParser`` or ``click`` command/group.

    Returns:
        CLI specification mapping command paths to option requirements.
    """

    if isinstance(obj, argparse.ArgumentParser):
        return _extract_argparse(obj)
    if click and isinstance(obj, click.core.Command):  # type: ignore[attr-defined]
        return _extract_click(obj)
    return {}


def diff_cli(old: CLI, new: CLI) -> List[Impact]:
    """Diff two CLI specifications.

    Args:
        old: CLI specification from the base revision.
        new: CLI specification from the head revision.

    Returns:
        List of impacts describing semantic version changes.
    """

    impacts: List[Impact] = []
    old_cmds, new_cmds = set(old), set(new)
    for cmd in old_cmds - new_cmds:
        impacts.append(Impact("major", cmd or "<root>", "Removed command"))
    for cmd in new_cmds - old_cmds:
        impacts.append(Impact("minor", cmd or "<root>", "Added command"))
    for cmd in old_cmds & new_cmds:
        o, n = old[cmd].options, new[cmd].options
        for opt in o.keys() - n.keys():
            impacts.append(Impact("major", cmd or "<root>", f"Removed option '{opt}'"))
        for opt in n.keys() - o.keys():
            severity = "major" if n[opt] else "minor"
            reason = "Added required option" if n[opt] else "Added optional option"
            impacts.append(Impact(severity, cmd or "<root>", reason))
        for opt in o.keys() & n.keys():
            if o[opt] != n[opt]:
                impacts.append(
                    Impact(
                        "major",
                        cmd or "<root>",
                        f"Option '{opt}' requirement changed",
                    )
                )
    return impacts


def _load_cli_from_source(src: str) -> CLI:
    """Execute source code and extract CLI specification.

    The code is executed in an isolated namespace.  A variable named ``parser``
    or ``cli`` may define the CLI object.  If it is callable, it will be
    invoked without arguments.

    Args:
        src: Python source defining the CLI.

    Returns:
        CLI specification, or an empty mapping if none found.
    """

    ns: Dict[str, Any] = {}
    try:
        exec(src, ns)
    except Exception:
        return {}
    obj = ns.get("parser") or ns.get("cli")
    if callable(obj):
        obj = obj()
    return extract_cli(obj) if obj is not None else {}


def build_cli_at_ref(ref: str, package: str) -> CLI:
    """Build CLI specification for a given git ref.

    Args:
        ref: Git reference to read from.
        package: Package name where ``cli.py`` resides.

    Returns:
        CLI specification extracted from that ref.
    """

    path = f"{package}/cli.py" if package else "cli.py"
    src = read_file_at_ref(ref, path)
    if src is None:
        return {}
    return _load_cli_from_source(src)


def diff_cli_at_refs(package: str, base: str, head: str) -> List[Impact]:
    """Compute CLI impacts between two git references.

    Args:
        package: Package containing the CLI module.
        base: Base git reference.
        head: Head git reference.

    Returns:
        List of impacts derived from CLI differences.
    """

    old = build_cli_at_ref(base, package)
    new = build_cli_at_ref(head, package)
    return diff_cli(old, new)
