"""Top-level package for :mod:`bumpwright`.

Exposes the ``main`` entry point used by the command-line interface. The
package is intended primarily for CLI usage rather than direct imports.
"""

from __future__ import annotations

from .cli import main

__all__ = ["__version__", "main"]

__version__ = "1.0.0"
