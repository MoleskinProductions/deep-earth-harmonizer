"""Tests for EarthEngineAdapter batch export, poll, GCS, and misc paths.

Covers lines missed by test_ee_error_paths.py: validate_credentials,
_fetch_direct success + fallback, _fetch_batch full path, _poll_task
states, _download_from_gcs, transform_to_grid, and fetch cache hit.
"""
import asyncio
import pytest
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

from deep_earth.providers.earth_engine import EarthEngineAdapter
from deep_earth.region import RegionContext


@pytest.fixture
def region():
    return RegionContext(
        lat_min=44.97, lat_max=44.98,
        lon_min=-93.27, lon_max=-93.26,
    )


@pytest.fixture
def large_region():
    """Region > 10 km2 to trigger batch path."""
    return RegionContext(
        lat_min=44.0, lat_max=45.0,
        lon_min=-94.0, lon_max=-93.0,
    )


@pytest.fixture
def adapter_initialized():
    """EarthEngineAdapter with init bypassed."""
    creds = MagicMock()
    creds.get_ee_service_account.return_value = "sa@test.iam.gserviceaccount.com"
    creds.get_ee_key_file.return_value = "/tmp/key.json"
    creds.get_gcs_bucket.return_value = "my-bucket"
    cache = MagicMock()
    cache.exists.return_value = False
    with patch("ee.ServiceAccountCredentials"), \
         patch("ee.Initialize"):
        adapter = EarthEngineAdapter(creds, cache)
        adapter._initialized = True
    return adapter


# ---------------------------------------------------------------------------
# validate_credentials
# ---------------------------------------------------------------------------

def test_validate_credentials_success():
    """Valid credentials + accessible collection -> True."""
    creds = MagicMock()
    creds.get_ee_service_account.return_value = "sa@p.iam.gserviceaccount.com"
    creds.get_ee_key_file.return_value = "/tmp/key.json"
    cache = MagicMock()

    with patch("ee.ServiceAccountCredentials"), \
         patch("ee.Initialize"), \
         patch("ee.ImageCollection") as mock_ic:
        mock_ic.return_value.limit.return_value.getInfo.return_value = {}
        adapter = EarthEngineAdapter(creds, cache)
        assert adapter.validate_credentials() is True


def test_validate_credentials_api_failure():
    """API call raises -> returns False."""
    creds = MagicMock()
    creds.get_ee_service_account.return_value = "sa@p.iam.gserviceaccount.com"
    creds.get_ee_key_file.return_value = "/tmp/key.json"
    cache = MagicMock()

    with patch("ee.ServiceAccountCredentials"), \
         patch("ee.Initialize"), \
         patch("ee.ImageCollection") as mock_ic:
        mock_ic.return_value.limit.return_value.getInfo.side_effect = (
            Exception("connection error")
        )
        adapter = EarthEngineAdapter(creds, cache)
        assert adapter.validate_credentials() is False


# ---------------------------------------------------------------------------
# fetch — cache hit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_cache_hit(region):
    """Cached result -> returns path without downloading."""
    creds = MagicMock()
    creds.get_ee_service_account.return_value = "sa@p.iam.gserviceaccount.com"
    creds.get_ee_key_file.return_value = "/tmp/key.json"
    cache = MagicMock()
    cache.exists.return_value = True
    cache.get_path.return_value = "/cached/embed.tif"

    with patch("ee.ServiceAccountCredentials"), \
         patch("ee.Initialize"):
        adapter = EarthEngineAdapter(creds, cache)
        result = await adapter.fetch(region, resolution=10)

    assert result == "/cached/embed.tif"


# ---------------------------------------------------------------------------
# _fetch_direct — success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_direct_success(adapter_initialized):
    """Download URL succeeds -> data saved to cache."""
    mock_image = MagicMock()
    mock_image.getDownloadURL.return_value = "https://ee.example.com/dl"
    mock_image.projection.return_value.nominalScale.return_value.getInfo.return_value = 10
    mock_image.projection.return_value.crs.return_value.getInfo.return_value = "EPSG:32615"

    adapter_initialized.cache.save.return_value = "/cache/embed.tif"

    with patch("deep_earth.providers.earth_engine.fetch_with_retry",
               new_callable=AsyncMock, return_value=b"tiff-bytes"):
        with patch("aiohttp.ClientSession"):
            result = await adapter_initialized._fetch_direct(
                mock_image, MagicMock(), "test_key",
            )

    assert result == "/cache/embed.tif"
    adapter_initialized.cache.save.assert_called_once_with(
        "test_key", b"tiff-bytes", category="embeddings",
    )


# ---------------------------------------------------------------------------
# _fetch_direct — fallback to batch on "Payload too large"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_direct_fallback_to_batch(adapter_initialized):
    """400/Payload too large -> falls back to _fetch_batch."""
    mock_image = MagicMock()
    mock_image.getDownloadURL.side_effect = Exception(
        "Payload too large (400)"
    )
    with patch.object(
        adapter_initialized, "_fetch_batch",
        new_callable=AsyncMock, return_value="/batch/result.tif",
    ) as mock_batch:
        result = await adapter_initialized._fetch_direct(
            mock_image, MagicMock(), "test_key",
        )

    assert result == "/batch/result.tif"
    mock_batch.assert_awaited_once()


# ---------------------------------------------------------------------------
# _fetch_batch — full success path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_batch_success(adapter_initialized):
    """Batch export -> poll COMPLETED -> download from GCS."""
    mock_image = MagicMock()
    mock_task = MagicMock()
    mock_task.id = "task123"

    with patch("ee.batch.Export.image.toCloudStorage", return_value=mock_task), \
         patch.object(
             adapter_initialized, "_poll_task",
             new_callable=AsyncMock,
             return_value={"state": "COMPLETED"},
         ), \
         patch.object(
             adapter_initialized, "_download_from_gcs",
             new_callable=AsyncMock,
             return_value="/cache/batch.tif",
         ):
        result = await adapter_initialized._fetch_batch(
            mock_image, MagicMock(), "test_key",
        )

    assert result == "/cache/batch.tif"
    mock_task.start.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_batch_task_failed(adapter_initialized):
    """Task status FAILED -> returns None."""
    mock_image = MagicMock()
    mock_task = MagicMock()
    mock_task.id = "task_fail"

    with patch("ee.batch.Export.image.toCloudStorage", return_value=mock_task), \
         patch.object(
             adapter_initialized, "_poll_task",
             new_callable=AsyncMock,
             return_value={
                 "state": "FAILED",
                 "error_message": "quota exceeded",
             },
         ):
        result = await adapter_initialized._fetch_batch(
            mock_image, MagicMock(), "test_key",
        )

    assert result is None


@pytest.mark.asyncio
async def test_fetch_batch_exception(adapter_initialized):
    """Exception during batch export -> returns None."""
    mock_image = MagicMock()

    with patch(
        "ee.batch.Export.image.toCloudStorage",
        side_effect=Exception("export API down"),
    ):
        result = await adapter_initialized._fetch_batch(
            mock_image, MagicMock(), "test_key",
        )

    assert result is None


# ---------------------------------------------------------------------------
# _poll_task
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_poll_task_completed(adapter_initialized):
    """Task completes on second poll."""
    task = MagicMock()
    task.id = "t1"
    task.status.side_effect = [
        {"state": "RUNNING"},
        {"state": "COMPLETED"},
    ]
    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await adapter_initialized._poll_task(task, timeout_secs=60)
    assert result["state"] == "COMPLETED"


@pytest.mark.asyncio
async def test_poll_task_failed(adapter_initialized):
    """Task reports FAILED."""
    task = MagicMock()
    task.id = "t2"
    task.status.return_value = {
        "state": "FAILED",
        "error_message": "out of memory",
    }
    result = await adapter_initialized._poll_task(task)
    assert result["state"] == "FAILED"


@pytest.mark.asyncio
async def test_poll_task_cancelled(adapter_initialized):
    """Task reports CANCELLED."""
    task = MagicMock()
    task.id = "t3"
    task.status.return_value = {"state": "CANCELLED"}
    result = await adapter_initialized._poll_task(task)
    assert result["state"] == "CANCELLED"


@pytest.mark.asyncio
async def test_poll_task_timeout(adapter_initialized):
    """Task never completes -> TimeoutError raised."""
    task = MagicMock()
    task.id = "t4"
    task.status.return_value = {"state": "RUNNING"}

    with patch("asyncio.sleep", new_callable=AsyncMock), \
         patch("time.time", side_effect=[0, 0, 9999]):
        with pytest.raises(TimeoutError, match="timed out"):
            await adapter_initialized._poll_task(task, timeout_secs=10)
    task.cancel.assert_called_once()


# ---------------------------------------------------------------------------
# _download_from_gcs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_download_from_gcs_success(adapter_initialized):
    """Downloads blob, saves to cache, and deletes blob from GCS."""
    mock_blob = MagicMock()
    mock_blob.download_as_bytes.return_value = b"geotiff-data"
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket

    adapter_initialized.cache.save.return_value = "/cache/dl.tif"

    with patch(
        "deep_earth.providers.earth_engine.storage.Client"
        ".from_service_account_json",
        return_value=mock_client,
    ):
        result = await adapter_initialized._download_from_gcs(
            "my-bucket", "file.tif", "cache_key",
        )

    assert result == "/cache/dl.tif"
    mock_blob.delete.assert_called_once()
    adapter_initialized.cache.save.assert_called_once_with(
        "cache_key", b"geotiff-data", category="embeddings",
    )


@pytest.mark.asyncio
async def test_download_from_gcs_cleanup_fails(adapter_initialized):
    """Blob delete fails -> still returns cache path (warning logged)."""
    mock_blob = MagicMock()
    mock_blob.download_as_bytes.return_value = b"geotiff-data"
    mock_blob.delete.side_effect = Exception("permission denied")
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket

    adapter_initialized.cache.save.return_value = "/cache/dl.tif"

    with patch(
        "deep_earth.providers.earth_engine.storage.Client"
        ".from_service_account_json",
        return_value=mock_client,
    ):
        result = await adapter_initialized._download_from_gcs(
            "my-bucket", "file.tif", "cache_key",
        )

    assert result == "/cache/dl.tif"


@pytest.mark.asyncio
async def test_download_from_gcs_missing_key():
    """No key file -> raises ValueError."""
    creds = MagicMock()
    creds.get_ee_key_file.return_value = None
    cache = MagicMock()
    adapter = EarthEngineAdapter(creds, cache)

    with pytest.raises(ValueError, match="GCS credentials missing"):
        await adapter._download_from_gcs("bucket", "blob", "key")


# ---------------------------------------------------------------------------
# transform_to_grid
# ---------------------------------------------------------------------------

def test_transform_to_grid(synthetic_embeddings):
    """Reads multi-band GeoTIFF into numpy array."""
    creds = MagicMock()
    cache = MagicMock()
    adapter = EarthEngineAdapter(creds, cache)
    grid = adapter.transform_to_grid(synthetic_embeddings, None)
    assert grid.shape == (64, 32, 32)
    assert grid.dtype == np.float32


# ---------------------------------------------------------------------------
# get_cache_key
# ---------------------------------------------------------------------------

def test_get_cache_key(region):
    """Cache key encodes all parameters."""
    creds = MagicMock()
    cache = MagicMock()
    adapter = EarthEngineAdapter(creds, cache)
    key = adapter.get_cache_key(region, 10, 2024)
    assert "44.97" in key
    assert "44.98" in key
    assert "10" in key
    assert "2024" in key
