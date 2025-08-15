"""Sphinx configuration for project documentation."""

# pylint: disable=invalid-name
project = "semverbump"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
templates_path = ["_templates"]
exclude_patterns: list[str] = []
html_theme = "alabaster"
