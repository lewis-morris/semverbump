"""Sphinx configuration for project documentation."""

from datetime import datetime

project = "semverbump"
author = "Lewis Morris"
copyright = f"{datetime.now():%Y}, {author}"
html_title = project

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Allow both .rst and .md sources
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Docstring style (Google by default, NumPy off unless you want both)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_special_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc / typehints behavior
autodoc_default_options = {
    "members": True,
    "inherited-members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"       # move hints into the description
autodoc_typehints_format = "short"      # short type names where possible
typehints_fully_qualified = False
always_document_param_types = True

# Optional: mock heavy imports during autodoc (uncomment and edit)
# autodoc_mock_imports = ["big_dep", "optional_dep"]

# MyST (Markdown) quality-of-life
myst_enable_extensions = [
    "colon_fence",     # ::: fenced blocks
    "deflist",         # definition lists
    "substitution",    # |subst| support
    "tasklist",        # - [ ] tasks
]

# -- HTML output -------------------------------------------------------------

html_theme = "furo"

# Code highlighting (light/dark)
highlight_language = "python3"
pygments_style = "sphinx"
pygments_dark_style = "monokai"

# Static assets (optional; create docs/_static if you need custom CSS/JS)
html_static_path = ["_static"]
html_logo = "_static/logo.png"
html_favicon = "_static/favicon.ico"

html_css_files = [
    "colours.css",
    "custom.css",
    "https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap",
]

colors = {
    "bg0": " #fbf1c7",
    "bg1": " #ebdbb2",
    "bg2": " #d5c4a1",
    "bg3": " #bdae93",
    "bg4": " #a89984",
    "gry": " #928374",
    "fg4": " #7c6f64",
    "fg3": " #665c54",
    "fg2": " #504945",
    "fg1": " #3c3836",
    "fg0": " #282828",
    "red": " #cc241d",
    "red2": " #9d0006",
    "orange": " #d65d0e",
    "orange2": " #af3a03",
    "yellow": " #d79921",
    "yellow2": " #b57614",
    "green": " #98971a",
    "green2": " #79740e",
    "aqua": " #689d6a",
    "aqua2": " #427b58",
    "blue": " #458588",
    "blue2": " #076678",
    "purple": " #b16286",
    "purple2": " #8f3f71",
}

html_theme_options = {
    "light_css_variables": {
        "font-stack": "JetBrains Mono, sans-serif",
        "font-stack--monospace": "JetBrains Mono, monospace",
        "color-brand-primary": colors["purple2"],
        "color-brand-content": colors["blue2"],
    },
    "dark_css_variables": {
        "color-brand-primary": colors["purple"],
        "color-brand-content": colors["blue"],
        "color-background-primary": colors["fg1"],
        "color-background-secondary": colors["fg0"],
        "color-foreground-primary": colors["bg0"],
        "color-foreground-secondary": colors["bg1"],
        "color-highlighted-background": colors["yellow"],
        "color-highlight-on-target": colors["fg2"],
    },
}
