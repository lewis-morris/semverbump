
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