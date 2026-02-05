"""Shared pytest fixtures for deep_earth tests.

Provides synthetic GeoTIFF generators, mock Overpass responses, and
Houdini module stubs so all provider tests run offline without
credentials or network access.
"""
import pytest
import numpy as np
import rasterio
from unittest.mock import MagicMock, patch
from deep_earth.region import RegionContext


# ---------------------------------------------------------------------------
# Region fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def region_minneapolis():
    """Small region in Minneapolis (< 10 km2)."""
    return RegionContext(
        lat_min=44.97, lat_max=44.98,
        lon_min=-93.27, lon_max=-93.26,
    )


# ---------------------------------------------------------------------------
# Synthetic GeoTIFF generators
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_dem(tmp_path, region_minneapolis):
    """Generate a single-band elevation GeoTIFF in WGS84.

    Returns the path to the file as a string.
    """
    path = tmp_path / "synthetic_dem.tif"
    rows, cols = 32, 32
    data = (np.random.rand(rows, cols) * 500 + 200).astype(np.float32)
    transform = rasterio.transform.from_bounds(
        region_minneapolis.lon_min, region_minneapolis.lat_min,
        region_minneapolis.lon_max, region_minneapolis.lat_max,
        cols, rows,
    )
    with rasterio.open(
        path, "w",
        driver="GTiff", height=rows, width=cols,
        count=1, dtype="float32",
        crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(data, 1)
    return str(path)


@pytest.fixture
def synthetic_embeddings(tmp_path, region_minneapolis):
    """Generate a 64-band embedding GeoTIFF in WGS84.

    Returns the path to the file as a string.
    """
    path = tmp_path / "synthetic_embed.tif"
    bands, rows, cols = 64, 32, 32
    data = np.random.rand(bands, rows, cols).astype(np.float32)
    transform = rasterio.transform.from_bounds(
        region_minneapolis.lon_min, region_minneapolis.lat_min,
        region_minneapolis.lon_max, region_minneapolis.lat_max,
        cols, rows,
    )
    with rasterio.open(
        path, "w",
        driver="GTiff", height=rows, width=cols,
        count=bands, dtype="float32",
        crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(data)
    return str(path)


# ---------------------------------------------------------------------------
# Mock Overpass API response
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_overpass_response():
    """Realistic Overpass JSON response with roads, buildings, and water."""
    return {
        "version": 0.6,
        "generator": "Overpass API",
        "elements": [
            {
                "type": "way",
                "id": 100001,
                "tags": {"highway": "residential", "name": "Elm St"},
                "geometry": [
                    {"lat": 44.975, "lon": -93.265},
                    {"lat": 44.976, "lon": -93.264},
                    {"lat": 44.977, "lon": -93.263},
                ],
            },
            {
                "type": "way",
                "id": 100002,
                "tags": {"highway": "primary", "name": "Main Ave"},
                "geometry": [
                    {"lat": 44.970, "lon": -93.270},
                    {"lat": 44.975, "lon": -93.265},
                ],
            },
            {
                "type": "way",
                "id": 200001,
                "tags": {"building": "yes", "height": "12"},
                "geometry": [
                    {"lat": 44.974, "lon": -93.266},
                    {"lat": 44.974, "lon": -93.265},
                    {"lat": 44.975, "lon": -93.265},
                    {"lat": 44.975, "lon": -93.266},
                    {"lat": 44.974, "lon": -93.266},
                ],
            },
            {
                "type": "way",
                "id": 300001,
                "tags": {"natural": "water", "name": "Lake"},
                "geometry": [
                    {"lat": 44.978, "lon": -93.268},
                    {"lat": 44.978, "lon": -93.267},
                    {"lat": 44.979, "lon": -93.267},
                    {"lat": 44.979, "lon": -93.268},
                    {"lat": 44.978, "lon": -93.268},
                ],
            },
            {
                "type": "way",
                "id": 400001,
                "tags": {"landuse": "residential"},
                "geometry": [
                    {"lat": 44.971, "lon": -93.269},
                    {"lat": 44.971, "lon": -93.266},
                    {"lat": 44.974, "lon": -93.266},
                    {"lat": 44.974, "lon": -93.269},
                    {"lat": 44.971, "lon": -93.269},
                ],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Houdini module stub
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_hou():
    """Provides a mock ``hou`` module and patches ``sys.modules``.

    Yields the mock so tests can inspect calls.  The patch is
    automatically cleaned up after the test.
    """
    hou = MagicMock()
    hou.primitiveType.Volume = "Volume"
    hou.attribType.Point = "Point"
    hou.attribType.Global = "Global"
    with patch.dict("sys.modules", {"hou": hou}):
        yield hou
