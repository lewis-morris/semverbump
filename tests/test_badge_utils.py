import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
sys.path.insert(0, str(DOCS))

from _utils.badge_utils import (  # noqa: E402
    generate_badges,
    read_coverage,
    read_project_metadata,
)


def test_read_project_metadata(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
version = "0.1.0"
classifiers = ["Programming Language :: Python :: 3.11"]
"""
    )
    version, license_name, python_versions = read_project_metadata(pyproject)
    assert version == "0.1.0"
    assert license_name == "MIT"
    assert python_versions == "3.11"


def test_read_coverage(tmp_path: Path) -> None:
    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text("<coverage line-rate='0.75'></coverage>")
    expected = 75.0
    assert read_coverage(coverage_xml) == expected


def test_generate_badges(tmp_path: Path) -> None:
    output = tmp_path / "badges"
    generate_badges(output, 80.0, "1.2.3", "MIT", "3.11")
    assert (output / "coverage.svg").exists()
    assert (output / "version.svg").exists()
    assert (output / "python.svg").exists()
    assert (output / "license.svg").exists()
