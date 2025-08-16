"""Generate project badges for documentation and README."""

from __future__ import annotations

import sys
from pathlib import Path

DOCS: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DOCS))

from _utils.badge_utils import (  # noqa: E402
    generate_badges,
    read_coverage,
    read_project_metadata,
)

ROOT: Path = DOCS.parent
PYPROJECT: Path = ROOT / "pyproject.toml"
COVERAGE_XML: Path = ROOT / "coverage.xml"
BADGE_DIR: Path = DOCS / "_static" / "badges"


def main() -> None:
    """Generate badges into the documentation static directory."""
    version, license_name, python_versions = read_project_metadata(PYPROJECT)
    coverage = read_coverage(COVERAGE_XML)
    generate_badges(BADGE_DIR, coverage, version, license_name, python_versions)


if __name__ == "__main__":
    main()
