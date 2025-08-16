"""Generate project badges for documentation and README."""

from __future__ import annotations

from pathlib import Path

from bumpwright.badge_utils import generate_badges, read_coverage, read_project_metadata

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
COVERAGE_XML = ROOT / "coverage.xml"
BADGE_DIR = ROOT / "docs" / "_static" / "badges"


def main() -> None:
    """Generate badges into the documentation static directory."""
    version, license_name, python_versions = read_project_metadata(PYPROJECT)
    coverage = read_coverage(COVERAGE_XML)
    generate_badges(BADGE_DIR, coverage, version, license_name, python_versions)


if __name__ == "__main__":
    main()
