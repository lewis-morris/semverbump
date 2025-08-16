"""Extract CLI command definitions for argparse and Click applications."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from dataclasses import dataclass

from ..compare import Impact
from ..config import Config
from ..gitutils import list_py_files_at_ref
from ..types import BumpLevel
from . import register
from .utils import _is_const_str, parse_python_source


@dataclass(frozen=True)
class Command:
    """Represent a CLI command and its options."""

    name: str
    options: dict[str, bool]  # True if required


def _extract_click(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Command | None:
    """Extract click command metadata from a function definition.

    Args:
        node: Function definition node, synchronous or asynchronous.

    Returns:
        :class:`Command` description if ``node`` defines a click command, otherwise
        ``None``.
    """

    cmd_name: str | None = None
    options: dict[str, bool] = {}
    is_click = False

    for deco in node.decorator_list:
        if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
            attr = deco.func
            if isinstance(attr.value, ast.Name) and attr.value.id == "click" and attr.attr in {"command", "group"}:
                is_click = True
                for kw in deco.keywords:
                    if kw.arg == "name" and _is_const_str(kw.value):
                        cmd_name = kw.value.value  # type: ignore[assignment]
            elif isinstance(attr.value, ast.Name) and attr.value.id == "click" and attr.attr == "option":
                name: str | None = None
                required = False
                for arg in deco.args:
                    if _is_const_str(arg) and arg.value.startswith("--"):
                        name = arg.value
                        break
                for kw in deco.keywords:
                    if kw.arg == "required" and isinstance(kw.value, ast.Constant):
                        required = bool(kw.value.value)
                if name:
                    options[name] = required
            elif isinstance(attr.value, ast.Name) and attr.value.id == "click" and attr.attr == "argument":
                if deco.args and _is_const_str(deco.args[0]):
                    name = deco.args[0].value  # type: ignore[assignment]
                    required = True
                    for kw in deco.keywords:
                        if kw.arg == "required" and isinstance(kw.value, ast.Constant):
                            required = bool(kw.value.value)
                    options[name] = required
    if is_click:
        if not cmd_name:
            cmd_name = node.name
        return Command(cmd_name, options)
    return None


def _extract_argparse(tree: ast.AST) -> dict[str, Command]:
    """Extract argparse commands from AST.

    Args:
        tree: Parsed module AST.

    Returns:
        Mapping of command name to :class:`Command` objects discovered via
        ``argparse``.
    """

    commands: dict[str, Command] = {}
    parsers: dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                attr = node.value.func
                if attr.attr == "add_parser" and node.value.args and _is_const_str(node.value.args[0]):
                    cmd_name = node.value.args[0].value  # type: ignore[assignment]
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            parsers[target.id] = cmd_name
                            commands[cmd_name] = Command(cmd_name, {})
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_argument" and isinstance(node.func.value, ast.Name) and node.func.value.id in parsers:
                parser_name = parsers[node.func.value.id]
                cmd = commands[parser_name]
                name: str | None = None
                required = False
                for arg in node.args:
                    if _is_const_str(arg):
                        if arg.value.startswith("--"):
                            if name is None or not name.startswith("--"):
                                name = arg.value
                        elif name is None:
                            name = arg.value
                            required = True
                for kw in node.keywords:
                    if kw.arg == "required" and isinstance(kw.value, ast.Constant):
                        required = bool(kw.value.value)
                    if kw.arg == "nargs" and isinstance(kw.value, ast.Constant):
                        if kw.value.value in ("?", "*"):
                            required = False
                        if kw.value.value == "+":
                            required = True
                if name:
                    cmd.options[name] = required
    return commands


def extract_cli_from_source(code: str | ast.AST) -> dict[str, Command]:
    """Extract command definitions from source code.

    Handles both synchronous and asynchronous click commands.

    Args:
        code: Python source text or a pre-parsed AST to analyze.

    Returns:
        Mapping of command name to :class:`Command` definitions.
    """

    tree = ast.parse(code) if isinstance(code, str) else code
    commands: dict[str, Command] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cmd = _extract_click(node)
            if cmd:
                commands[cmd.name] = cmd
    commands.update(_extract_argparse(tree))
    return commands


def diff_cli(old: dict[str, Command], new: dict[str, Command]) -> list[Impact]:
    """Compare CLI definitions and compute impacts.

    Args:
        old: Command mapping for the base reference.
        new: Command mapping for the head reference.

    Returns:
        List of detected impacts between the two mappings.
    """

    impacts: list[Impact] = []
    for name in old.keys() - new.keys():
        impacts.append(Impact("major", name, "Removed command"))
    for name in new.keys() - old.keys():
        impacts.append(Impact("minor", name, "Added command"))
    for name in old.keys() & new.keys():
        op = old[name].options
        np = new[name].options
        for opt in op.keys() - np.keys():
            severity: BumpLevel = "major" if op[opt] else "minor"
            reason = "Removed required option" if op[opt] else "Removed optional option"
            impacts.append(Impact(severity, name, f"{reason} '{opt}'"))
        for opt in np.keys() - op.keys():
            severity: BumpLevel = "major" if np[opt] else "minor"
            reason = "Added required option" if np[opt] else "Added optional option"
            impacts.append(Impact(severity, name, f"{reason} '{opt}'"))
        for opt in op.keys() & np.keys():
            if op[opt] and not np[opt]:
                impacts.append(Impact("minor", name, f"Option '{opt}' became optional"))
            if not op[opt] and np[opt]:
                impacts.append(Impact("major", name, f"Option '{opt}' became required"))
    return impacts


def _build_cli_at_ref(ref: str, roots: Iterable[str], ignores: Iterable[str]) -> dict[str, Command]:
    """Collect commands for all modules at a git ref.

    Args:
        ref: Git reference to inspect.
        roots: Root directories to scan.
        ignores: Glob patterns to exclude.

    Returns:
        Mapping of command name to :class:`Command` objects present at ``ref``.
    """

    out: dict[str, Command] = {}
    for path in list_py_files_at_ref(ref, roots, ignore_globs=ignores):
        tree = parse_python_source(ref, path)
        if tree is not None:
            out.update(extract_cli_from_source(tree))
    return out


@register("cli", "Analyze command-line interfaces for changes.")
class CLIAnalyser:
    """Analyser plugin for command-line interfaces."""

    def __init__(self, cfg: Config) -> None:
        """Initialize the analyser with configuration."""
        self.cfg = cfg

    def collect(self, ref: str) -> dict[str, Command]:
        """Collect CLI commands at the given ref.

        Args:
            ref: Git reference to inspect.

        Returns:
            Mapping of command name to :class:`Command` objects.
        """

        return _build_cli_at_ref(ref, self.cfg.project.public_roots, self.cfg.ignore.paths)

    def compare(self, old: dict[str, Command], new: dict[str, Command]) -> list[Impact]:
        """Compare two command mappings and return impacts.

        Args:
            old: Baseline command mapping.
            new: Updated command mapping.

        Returns:
            List of impacts describing CLI changes.
        """

        return diff_cli(old, new)
