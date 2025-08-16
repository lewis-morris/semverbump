"""Sphinx configuration for project documentation."""

import inspect
import os
import sys
from datetime import datetime

import bumpwright

project = "bumpwright"
author = "Lewis Morris (arched.dev)"
copyright = f"{datetime.now():%Y}, {author}"
html_title = project

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_wagtail_theme",
    "sphinx.ext.autosummary",
    "sphinxcontrib.autoprogram",
    "sphinx.ext.linkcode",
    "sphinx_click",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
autosummary_generate = True

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

# Cross-referencing and external links
autosectionlabel_prefix_document = True
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "click": ("https://click.palletsprojects.com/en/latest/", None),
    "flask": ("https://flask.palletsprojects.com/en/latest/", None),
    "fastapi": ("https://fastapi.tiangolo.com/", None),
    "alembic": ("https://alembic.sqlalchemy.org/en/latest/", None),
}

# Autodoc / typehints behaviour
autodoc_default_options = {
    "members": True,
    "inherited-members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"  # move hints into the description
autodoc_typehints_format = "short"  # short type names where possible
typehints_fully_qualified = False
always_document_param_types = True

# Optional: mock heavy imports during autodoc (uncomment and edit)
# autodoc_mock_imports = ["big_dep", "optional_dep"]

# MyST (Markdown) quality-of-life
myst_enable_extensions = [
    "colon_fence",  # ::: fenced blocks
    "deflist",  # definition lists
    "substitution",  # |subst| support
    "tasklist",  # - [ ] tasks
]

# -- HTML output -------------------------------------------------------------

html_theme = "sphinx_wagtail_theme"

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


html_theme_options = dict(
    project_name="bumpwright",
    logo="logo_bg.png",
    logo_alt="bumpwright logo",
    logo_height=70,
    logo_url="/",
    logo_width=70,
    github_url="https://github.com/lewis-morris/bumpwright",
    footer_links=",".join(
        [
            "About Us|https://arched.dev",
        ]
    ),
)


def linkcode_resolve(domain: str, info: dict[str, str]) -> str | None:
    """Resolve GitHub source links for documented objects.

    Args:
        domain: The documentation domain (e.g., ``"py"``).
        info: Mapping with module and object path information.

    Returns:
        A URL pointing to the object on GitHub, or ``None`` if not resolvable.
    """
    if domain != "py" or not info.get("module"):
        return None

    module = sys.modules.get(info["module"])
    if module is None:
        return None

    obj = module
    for part in info["fullname"].split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None

    try:
        filename = inspect.getsourcefile(obj)
        source, lineno = inspect.getsourcelines(obj)
    except OSError:
        return None

    relpath = os.path.relpath(filename, start=os.path.dirname(bumpwright.__file__))
    end_line = lineno + len(source) - 1
    return (
        "https://github.com/lewis-morris/bumpwright/blob/main/bumpwright/"
        f"{relpath}#L{lineno}-L{end_line}"
    )
