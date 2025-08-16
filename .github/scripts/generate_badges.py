#!/usr/bin/env python3
"""
Generate simple SVG badges for:
- version
- license
- supported Python versions
- coverage (if coverage.xml is present; otherwise "—")

Usage:
    python .github/scripts/generate_badges.py [OUTPUT_DIR]

Defaults to: docs/_static/badges
"""

from __future__ import annotations

from importlib.metadata import version as dist_version  # py3.11+
import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Optional

# tomllib is stdlib in 3.11+
try:
    import tomllib  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    print("Python 3.11+ required for tomllib", file=sys.stderr)
    raise


def read_pyproject() -> dict:
    pp = Path("pyproject.toml")
    if not pp.exists():
        return {}
    return tomllib.loads(pp.read_text(encoding="utf-8"))


def extract_version(project: dict) -> str:
    # PEP 621: project.version OR dynamic
    version = project.get("version")
    if version:
        return str(version)

    # Try dynamic via importlib.metadata if project has a name and is installed
    name = project.get("name")
    if name:
        try:
            return dist_version(name)
        except Exception:
            pass

    return "unknown"


def extract_license(project: dict) -> str:
    lic = project.get("license")
    if isinstance(lic, dict):
        # license = {text="MIT"} or {file="LICENCE"}
        if "text" in lic and lic["text"]:
            return str(lic["text"])
        if "file" in lic and lic["file"]:
            f = Path(lic["file"])
            constraint_val = 40
            if f.exists():
                # read first non-empty line as short name
                for line in f.read_text(encoding="utf-8").splitlines():
                    ln = line.strip()
                    if ln:
                        return ln[:constraint_val] + ("…" if len(ln) > constraint_val else "")
            return str(lic["file"])
    elif isinstance(lic, str):
        return lic
    return "UNKNOWN"


def extract_python_versions(project: dict) -> str:
    # Prefer explicit trove classifiers
    classifiers: Iterable[str] = project.get("classifiers", []) or []
    py_vers = []
    for c in classifiers:
        m = re.fullmatch(r"Programming Language :: Python :: (\d\.\d+)", c)
        if m:
            py_vers.append(m.group(1))

    if py_vers:
        # unique + sorted semver-ish
        py_vers = sorted(set(py_vers), key=lambda s: tuple(map(int, s.split("."))))
        return ", ".join(py_vers)

    # Fallback: project.requires-python (e.g. ">=3.9")
    req = project.get("requires-python")
    if req:
        return str(req)

    return "unspecified"


def find_coverage() -> Optional[str]:
    """
    Look for Cobertura-style coverage.xml and return a percentage string.
    If not found or parse fails, return None.
    """
    cov = Path("coverage.xml")
    if not cov.exists():
        return None

    try:
        root = ET.parse(cov).getroot()
        # Cobertura root has attributes like line-rate="0.87"
        lr = root.attrib.get("line-rate")
        if lr is not None:
            pct = round(float(lr) * 100)
            return f"{pct}%"
    except Exception:
        return None
    return None


def svg_badge(left: str, right: str, color: str = "#4c1") -> str:
    """
    Minimal flat-style SVG badge generator (no external deps).
    Width is a heuristic based on text length — fine for CI.
    """
    left = html.escape(left)
    right = html.escape(right)

    def width(txt: str) -> int:
        # 6px per char + padding
        return 6 * len(txt) + 10

    lw = width(left)
    rw = width(right)
    total = lw + rw

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20" role="img" aria-label="{left}: {right}">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="m"><rect width="{total}" height="20" rx="3" fill="#fff"/></mask>
  <g mask="url(#m)">
    <rect width="{lw}" height="20" fill="#555"/>
    <rect x="{lw}" width="{rw}" height="20" fill="{color}"/>
    <rect width="{total}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{lw/2:.1f}" y="14">{left}</text>
    <text x="{lw + rw/2:.1f}" y="14">{right}</text>
  </g>
</svg>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("output", nargs="?", default="docs/_static/badges", help="Output directory for SVG badges")
    args = ap.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    pp = read_pyproject()
    project = pp.get("project", {})

    version = extract_version(project)
    license_name = extract_license(project)
    python_text = extract_python_versions(project)
    coverage_text = find_coverage() or "—"

    (out_dir / "version.svg").write_text(svg_badge("version", version, "#007ec6"), encoding="utf-8")
    (out_dir / "license.svg").write_text(svg_badge("license", license_name, "#97CA00"), encoding="utf-8")
    (out_dir / "python.svg").write_text(svg_badge("python", python_text, "#306998"), encoding="utf-8")
    (out_dir / "coverage.svg").write_text(svg_badge("coverage", coverage_text, "#4c1"), encoding="utf-8")

    print(f"Generated: {[p.name for p in out_dir.glob('*.svg')]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
