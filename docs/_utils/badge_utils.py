"""Utilities for generating project badges.

This module provides helper functions used to generate SVG badges
containing coverage, version and other metadata.  The functions are kept
simple so they can be tested independently from the workflow script.
"""

from __future__ import annotations

import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple

import anybadge


def read_project_metadata(pyproject_path: Path) -> Tuple[str, str, str]:
    """Extract metadata from ``pyproject.toml``.

    Args:
        pyproject_path: Path to the ``pyproject.toml`` file.

    Returns:
        A tuple of version string, license name and supported Python versions.
    """
    data = tomllib.loads(pyproject_path.read_text())
    project = data.get("project", {})
    version: str = project.get("version", "0.0.0")
    license_name: str = "MIT"
    classifiers = project.get("classifiers", [])
    py_versions = [
        c.split("::")[-1].strip()
        for c in classifiers
        if c.strip().startswith("Programming Language :: Python :: 3.")
    ]
    python_versions = ", ".join(py_versions)
    return version, license_name, python_versions


def read_coverage(xml_path: Path) -> float:
    """Read coverage percentage from ``coverage.xml``.

    Args:
        xml_path: Path to the coverage XML report.

    Returns:
        The coverage percentage between 0 and 100.
    """
    root = ET.parse(xml_path).getroot()
    line_rate = float(root.get("line-rate", 0.0))
    return round(line_rate * 100, 2)


def generate_badges(
    output_dir: Path,
    coverage: float,
    version: str,
    license_name: str,
    python_versions: str,
) -> None:
    """Create SVG badges for project metadata.

    Args:
        output_dir: Directory to place generated badges in.
        coverage: Coverage percentage to display.
        version: Project version string.
        license_name: Name of the project's license.
        python_versions: Supported Python versions string.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    coverage_badge = anybadge.Badge(
        "coverage",
        f"{coverage:.0f}%",
        thresholds={50: "red", 80: "orange", 90: "yellow", 95: "green"},
    )
    coverage_badge.write_badge(output_dir / "coverage.svg", overwrite=True)

    anybadge.Badge("version", version, default_color="blue").write_badge(
        output_dir / "version.svg", overwrite=True
    )
    anybadge.Badge("python", python_versions, default_color="blue").write_badge(
        output_dir / "python.svg", overwrite=True
    )
    anybadge.Badge("license", license_name, default_color="blue").write_badge(
        output_dir / "license.svg", overwrite=True
    )
