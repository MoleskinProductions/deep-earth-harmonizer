"""Backward-compatibility shim for HDA code referencing the old module name."""
from deep_earth.region import RegionContext as CoordinateManager  # noqa: F401

__all__ = ["CoordinateManager"]
