import pytest
import json
import subprocess
import sys
from unittest.mock import MagicMock, patch, AsyncMock

def test_cli_help():
    """Test that the CLI help command works."""
    result = subprocess.run(
        [sys.executable, "-m", "deep_earth", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert "--bbox" in result.stdout

def test_cli_parse_bbox():
    """Test that the CLI correctly parses the bbox argument."""
    with patch("deep_earth.cli.main_logic") as mock_main:
        from deep_earth.cli import main
        
        # Simulate command line arguments
        test_args = ["--bbox", "45.0,-93.0,45.1,-92.9", "--resolution", "10"]
        with patch.object(sys, 'argv', ["deep_earth"] + test_args):
            main()
            
        mock_main.assert_called_once()
        args = mock_main.call_args[0][0]
        assert args.bbox == "45.0,-93.0,45.1,-92.9"
        assert args.resolution == 10.0

@pytest.mark.asyncio
async def test_cli_execution_summary(tmp_path):
    """Test that the CLI outputs a valid JSON summary."""
    # This might be better as an integration test or using mocks
    # For now, let's mock the adapters to avoid network calls
    
    mock_srtm = MagicMock()
    mock_srtm.fetch = AsyncMock(return_value=str(tmp_path / "srtm.tif"))
    
    mock_gee = MagicMock()
    mock_gee.fetch = AsyncMock(return_value=str(tmp_path / "gee.tif"))
    
    mock_osm = MagicMock()
    mock_osm.fetch = AsyncMock(return_value={"elements": []})
    mock_osm.get_cache_key.return_value = "osm_key"
    
    with patch("deep_earth.cli.SRTMAdapter", return_value=mock_srtm), \
         patch("deep_earth.cli.EarthEngineAdapter", return_value=mock_gee), \
         patch("deep_earth.cli.OverpassAdapter", return_value=mock_osm), \
         patch("deep_earth.cli.CredentialsManager"), \
         patch("deep_earth.cli.CacheManager") as MockCache:
        
        mock_cache_instance = MockCache.return_value
        mock_cache_instance.get_path.return_value = str(tmp_path / "osm.json")
        
        from deep_earth.cli import run_fetch_all
        from deep_earth.bbox import BoundingBox
        
        bbox = BoundingBox(45.0, 45.1, -93.0, -92.9)
        results = await run_fetch_all(bbox, resolution=10, year=2023)
        
        assert "srtm" in results
        assert "embeddings" in results
        assert "osm" in results
        assert results["srtm"].endswith("srtm.tif")
