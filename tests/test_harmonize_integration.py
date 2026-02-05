"""Integration tests for Harmonizer using synthetic GeoTIFF fixtures.

Exercises the full harmonization pipeline (resample + process_fetch_result
+ quality layer) offline using conftest-generated data.
"""
import pytest
import numpy as np
from deep_earth.harmonize import Harmonizer, FetchResult
from deep_earth.providers.osm import OverpassAdapter


def test_harmonize_synthetic_dem(region_minneapolis, synthetic_dem):
    """Resample a synthetic DEM through the full pipeline."""
    h = Harmonizer(region_minneapolis, resolution=10)
    grid, result = h.process_fetch_result(synthetic_dem, "srtm", bands=1)

    assert result.ok
    assert grid is not None
    assert grid.shape == (h.height, h.width)
    assert np.any(grid > 0)


def test_harmonize_synthetic_embeddings(
    region_minneapolis, synthetic_embeddings,
):
    """Resample synthetic 64-band embeddings through the full pipeline."""
    h = Harmonizer(region_minneapolis, resolution=10)
    grid, result = h.process_fetch_result(
        synthetic_embeddings, "gee", bands=list(range(1, 65)),
    )

    assert result.ok
    assert grid is not None
    assert grid.shape == (64, h.height, h.width)


def test_quality_layer_partial_dem_only(
    region_minneapolis, synthetic_dem,
):
    """Quality layer when only DEM succeeded."""
    h = Harmonizer(region_minneapolis, resolution=10)
    height_grid, srtm_r = h.process_fetch_result(
        synthetic_dem, "srtm", bands=1,
    )
    _, gee_r = h.process_fetch_result(None, "gee")

    quality = h.compute_quality_layer(
        height_grid if srtm_r.ok else None,
        None,
    )
    assert np.all(quality == 0.25)


def test_quality_layer_all_sources(
    region_minneapolis, synthetic_dem, synthetic_embeddings,
    mock_overpass_response,
):
    """Quality layer when all three sources succeed."""
    h = Harmonizer(region_minneapolis, resolution=10)
    height_grid, _ = h.process_fetch_result(
        synthetic_dem, "srtm", bands=1,
    )
    embed_grid, _ = h.process_fetch_result(
        synthetic_embeddings, "gee", bands=list(range(1, 65)),
    )

    # Add OSM layers via adapter
    adapter = OverpassAdapter()
    features = adapter._parse_elements(
        mock_overpass_response["elements"],
    )
    layers = adapter.transform_to_grid(features, h)
    h.add_layers(layers)

    quality = h.compute_quality_layer(height_grid, embed_grid)
    assert np.all(quality == 1.0)


def test_full_pipeline_with_provider_failure(
    region_minneapolis, synthetic_dem,
):
    """DEM succeeds, GEE raises, OSM empty -> quality 0.25."""
    h = Harmonizer(region_minneapolis, resolution=10)

    height_grid, srtm_r = h.process_fetch_result(
        synthetic_dem, "srtm", bands=1,
    )
    embed_grid, gee_r = h.process_fetch_result(
        RuntimeError("GEE unavailable"), "gee",
    )

    assert srtm_r.ok
    assert not gee_r.ok
    assert embed_grid is None

    if embed_grid is None:
        embed_grid = np.zeros(
            (64, h.height, h.width), dtype=np.float32,
        )

    quality = h.compute_quality_layer(
        height_grid if srtm_r.ok else None,
        embed_grid if gee_r.ok else None,
    )
    assert np.all(quality == 0.25)
