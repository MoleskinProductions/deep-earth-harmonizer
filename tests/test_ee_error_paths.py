"""Tests for EarthEngineAdapter fail-graceful error paths (Phase 8.1).

Verifies that missing credentials, empty collections, batch failures,
and missing GCS buckets all return None instead of raising, allowing
the DEM/OSM-only pipeline to continue.
"""
import pytest
from unittest.mock import patch, MagicMock
from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.region import RegionContext


@pytest.fixture
def region():
    return RegionContext(
        lat_min=44.97, lat_max=44.98,
        lon_min=-93.27, lon_max=-93.26,
    )


@pytest.fixture
def mock_cache():
    cache = MagicMock()
    cache.exists.return_value = False
    return cache


# ---- Missing / invalid credentials ----

@pytest.mark.asyncio
async def test_fetch_returns_none_when_no_credentials(region, mock_cache):
    """No service account or key file -> fetch returns None."""
    creds = MagicMock()
    creds.get_ee_service_account.return_value = None
    creds.get_ee_key_file.return_value = None

    adapter = EarthEngineAdapter(creds, mock_cache)
    result = await adapter.fetch(region, resolution=10, year=2023)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_returns_none_when_init_raises(region, mock_cache):
    """ee.Initialize raises -> fetch returns None."""
    creds = MagicMock()
    creds.get_ee_service_account.return_value = "test@test.iam.gserviceaccount.com"
    creds.get_ee_key_file.return_value = "/tmp/key.json"

    with patch("ee.ServiceAccountCredentials"):
        with patch("ee.Initialize", side_effect=Exception("auth error")):
            adapter = EarthEngineAdapter(creds, mock_cache)
            result = await adapter.fetch(region, resolution=10, year=2023)

    assert result is None


@pytest.mark.asyncio
async def test_init_failure_is_sticky(region, mock_cache):
    """Once initialization fails, subsequent fetches also return None."""
    creds = MagicMock()
    creds.get_ee_service_account.return_value = None
    creds.get_ee_key_file.return_value = None

    adapter = EarthEngineAdapter(creds, mock_cache)
    r1 = await adapter.fetch(region, resolution=10)
    r2 = await adapter.fetch(region, resolution=10)

    assert r1 is None
    assert r2 is None
    assert adapter._init_error is not None


# ---- Empty collection ----

@pytest.mark.asyncio
async def test_fetch_returns_none_on_empty_collection(region, mock_cache):
    """No imagery for given year -> fetch returns None."""
    creds = MagicMock()
    creds.get_ee_service_account.return_value = "sa@test.iam.gserviceaccount.com"
    creds.get_ee_key_file.return_value = "/tmp/key.json"

    with patch("ee.ServiceAccountCredentials"), \
         patch("ee.Initialize"), \
         patch("ee.Geometry.Rectangle"), \
         patch("ee.ImageCollection") as mock_coll_cls:
        mock_coll = MagicMock()
        mock_coll_cls.return_value = mock_coll
        mock_coll.filterDate.return_value = mock_coll
        mock_coll.size.return_value.getInfo.return_value = 0

        adapter = EarthEngineAdapter(creds, mock_cache)
        result = await adapter.fetch(region, resolution=10, year=2099)

    assert result is None


# ---- Batch export: no GCS bucket ----

@pytest.mark.asyncio
async def test_fetch_batch_returns_none_without_bucket(mock_cache):
    """Large region + no GCS bucket -> returns None."""
    # Use a large region (> 10 km2) to trigger batch path
    large_region = RegionContext(
        lat_min=44.0, lat_max=45.0,
        lon_min=-94.0, lon_max=-93.0,
    )
    creds = MagicMock()
    creds.get_ee_service_account.return_value = "sa@test.iam.gserviceaccount.com"
    creds.get_ee_key_file.return_value = "/tmp/key.json"
    creds.get_gcs_bucket.return_value = None

    with patch("ee.ServiceAccountCredentials"), \
         patch("ee.Initialize"), \
         patch("ee.Geometry.Rectangle"), \
         patch("ee.ImageCollection") as mock_coll_cls:
        mock_image = MagicMock()
        mock_coll = MagicMock()
        mock_coll_cls.return_value = mock_coll
        mock_coll.filterDate.return_value = mock_coll
        mock_coll.size.return_value.getInfo.return_value = 1
        mock_coll.mosaic.return_value = mock_image
        mock_image.clip.return_value = mock_image
        mock_image.reproject.return_value = mock_image

        adapter = EarthEngineAdapter(creds, mock_cache)
        result = await adapter.fetch(
            large_region, resolution=10, year=2023,
        )

    assert result is None


# ---- Direct fetch failure (non-recoverable) ----

@pytest.mark.asyncio
async def test_fetch_direct_returns_none_on_error(region, mock_cache):
    """Direct download fails with non-size error -> returns None."""
    creds = MagicMock()
    creds.get_ee_service_account.return_value = "sa@test.iam.gserviceaccount.com"
    creds.get_ee_key_file.return_value = "/tmp/key.json"

    with patch("ee.ServiceAccountCredentials"), \
         patch("ee.Initialize"):
        adapter = EarthEngineAdapter(creds, mock_cache)
        mock_image = MagicMock()
        mock_image.getDownloadURL.side_effect = Exception(
            "Computation timed out"
        )

        result = await adapter._fetch_direct(
            mock_image, MagicMock(), "test_key",
        )

    assert result is None
