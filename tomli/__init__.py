"""A tiny subset of the :mod:`tomli` API for tests.

The real project provides a TOML parser for Python versions lacking
``tomllib``. For the purposes of the test suite we only need ``loads`` which
can be satisfied by the standard library module.
"""

from __future__ import annotations

import tomllib as _tomllib

loads = _tomllib.loads

__all__ = ["loads"]
