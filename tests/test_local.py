"""Tests for LocalFileAdapter (local raster ingestion)."""

import os

import numpy as np
import pytest
import rasterio

from deep_earth.cache import CacheManager
from deep_earth.providers.local import LocalFileAdapter
from deep_earth.region import RegionContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_synthetic_tif(
    path: str,
    region: RegionContext,
    *,
    bands: int = 1,
    rows: int = 16,
    cols: int = 16,
) -> str:
    """Write a small synthetic GeoTIFF in WGS84 and return its path."""
    data = np.random.rand(bands, rows, cols).astype(np.float32)
    transform = rasterio.transform.from_bounds(
        region.lon_min, region.lat_min,
        region.lon_max, region.lat_max,
        cols, rows,
    )
    with rasterio.open(
        path, "w",
        driver="GTiff", height=rows, width=cols,
        count=bands, dtype="float32",
        crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(data)
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLocalFileAdapter:
    """Unit tests for LocalFileAdapter."""

    def test_validate_credentials_always_true(self):
        adapter = LocalFileAdapter()
        assert adapter.validate_credentials() is True

    def test_get_cache_key_deterministic(self, region_minneapolis):
        adapter = LocalFileAdapter()
        key1 = adapter.get_cache_key(
            region_minneapolis, 10.0, "/data/rasters",
        )
        key2 = adapter.get_cache_key(
            region_minneapolis, 10.0, "/data/rasters",
        )
        assert key1 == key2
        assert "local_" in key1

    @pytest.mark.asyncio
    async def test_fetch_single_file(
        self, tmp_path, region_minneapolis,
    ):
        cache = CacheManager(str(tmp_path / "cache"))
        adapter = LocalFileAdapter(cache)

        tif = _write_synthetic_tif(
            str(tmp_path / "elev.tif"), region_minneapolis,
        )

        result = await adapter.fetch(
            region_minneapolis, 30.0, tif,
        )

        assert result is not None
        assert os.path.exists(result)
        with rasterio.open(result) as src:
            assert src.count == 1

    @pytest.mark.asyncio
    async def test_fetch_directory_multiple_tifs(
        self, tmp_path, region_minneapolis,
    ):
        cache = CacheManager(str(tmp_path / "cache"))
        adapter = LocalFileAdapter(cache)

        subdir = tmp_path / "rasters"
        subdir.mkdir()
        _write_synthetic_tif(
            str(subdir / "a.tif"), region_minneapolis,
        )
        _write_synthetic_tif(
            str(subdir / "b.tif"), region_minneapolis,
        )

        result = await adapter.fetch(
            region_minneapolis, 30.0, str(subdir),
        )

        assert result is not None
        assert os.path.exists(result)

    @pytest.mark.asyncio
    async def test_fetch_nonexistent_path_returns_none(
        self, region_minneapolis,
    ):
        adapter = LocalFileAdapter()
        result = await adapter.fetch(
            region_minneapolis, 30.0, "/nonexistent/path",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_empty_directory_returns_none(
        self, tmp_path, region_minneapolis,
    ):
        empty = tmp_path / "empty"
        empty.mkdir()
        adapter = LocalFileAdapter()
        result = await adapter.fetch(
            region_minneapolis, 30.0, str(empty),
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_cache_hit_returns_cached_path(
        self, tmp_path, region_minneapolis,
    ):
        cache = CacheManager(str(tmp_path / "cache"))
        adapter = LocalFileAdapter(cache)

        tif = _write_synthetic_tif(
            str(tmp_path / "elev.tif"), region_minneapolis,
        )

        first = await adapter.fetch(
            region_minneapolis, 30.0, tif,
        )
        second = await adapter.fetch(
            region_minneapolis, 30.0, tif,
        )

        assert first == second

    def test_transform_to_grid_reads_geotiff(
        self, tmp_path, region_minneapolis,
    ):
        adapter = LocalFileAdapter()
        tif = _write_synthetic_tif(
            str(tmp_path / "grid.tif"),
            region_minneapolis,
            bands=3, rows=8, cols=8,
        )

        arr = adapter.transform_to_grid(tif, target_grid=None)
        assert arr.shape == (3, 8, 8)
