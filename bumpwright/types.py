"""Common type aliases for bumpwright."""

from __future__ import annotations

from typing import Literal

BumpLevel = Literal["major", "minor", "patch"]
"""Semantic version bump levels."""
