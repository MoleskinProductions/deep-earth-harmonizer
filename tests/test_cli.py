import os
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
        from deep_earth.region import RegionContext as BoundingBox

        bbox = BoundingBox(45.0, 45.1, -93.0, -92.9)
        output = await run_fetch_all(bbox, resolution=10, year=2023)

        results = output["results"]
        assert "srtm" in results
        assert "embeddings" in results
        assert "osm" in results
        assert results["srtm"].endswith("srtm.tif")
        assert "errors" not in output


@pytest.mark.asyncio
async def test_cli_partial_failure_includes_errors():
    """When a provider raises, output includes errors dict."""
    mock_srtm = MagicMock()
    mock_srtm.fetch = AsyncMock(
        side_effect=ValueError("API key missing"),
    )

    mock_gee = MagicMock()
    mock_gee.fetch = AsyncMock(return_value=None)

    mock_osm = MagicMock()
    mock_osm.fetch = AsyncMock(return_value={"elements": []})
    mock_osm.get_cache_key.return_value = "osm_key"

    with patch("deep_earth.cli.SRTMAdapter", return_value=mock_srtm), \
         patch("deep_earth.cli.EarthEngineAdapter", return_value=mock_gee), \
         patch("deep_earth.cli.OverpassAdapter", return_value=mock_osm), \
         patch("deep_earth.cli.CredentialsManager"), \
         patch("deep_earth.cli.CacheManager") as MockCache:

        mock_cache_instance = MockCache.return_value
        mock_cache_instance.get_path.return_value = "/tmp/osm.json"

        from deep_earth.cli import run_fetch_all
        from deep_earth.region import RegionContext

        bbox = RegionContext(45.0, 45.1, -93.0, -92.9)
        output = await run_fetch_all(bbox, resolution=10, year=2023)

        assert output["results"]["srtm"] is None
        assert output["results"]["embeddings"] is None
        assert "errors" in output
        assert "API key missing" in output["errors"]["srtm"]
        assert "embeddings" in output["errors"]


def test_cli_invalid_bbox_exits_cleanly(capsys):
    """Invalid bbox prints error message and exits with code 1."""
    from deep_earth.cli import main_logic

    args = MagicMock()
    args.bbox = "not,a,valid"

    with pytest.raises(SystemExit) as exc_info:
        main_logic(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Invalid bbox format" in captured.out


def test_cli_fatal_error_outputs_json(capsys):
    """Unexpected error in run_fetch_all prints JSON error and exits."""
    from deep_earth.cli import main_logic

    args = MagicMock()
    args.bbox = "45.0,-93.0,45.1,-92.9"
    args.resolution = 10.0
    args.year = 2023

    with patch("deep_earth.cli.setup_logging"), \
         patch("deep_earth.cli.asyncio.run",
               side_effect=RuntimeError("cache dir missing")):
        with pytest.raises(SystemExit) as exc_info:
            main_logic(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "cache dir missing" in output["error"]


def test_cli_run_preview_success(tmp_path, capsys):
    """_run_preview generates a preview image from SRTM data."""
    import numpy as np
    import rasterio

    # Create a synthetic DEM
    dem_path = str(tmp_path / "srtm.tif")
    data = np.random.rand(10, 10).astype(np.float32) * 100
    with rasterio.open(
        dem_path, "w", driver="GTiff",
        height=10, width=10, count=1, dtype="float32",
    ) as dst:
        dst.write(data, 1)

    preview_out = str(tmp_path / "preview.png")
    output = {"results": {"srtm": dem_path}}

    from deep_earth.cli import _run_preview
    _run_preview(output, preview_out)

    captured = capsys.readouterr()
    assert f"Preview saved to {preview_out}" in captured.out
    assert os.path.exists(preview_out)


def test_cli_run_preview_no_srtm(capsys):
    """_run_preview with no SRTM data logs warning, does not crash."""
    from deep_earth.cli import _run_preview
    _run_preview({"results": {}}, "/tmp/nope.png")
    # Should not crash; warning is logged but not printed to stdout


def test_cli_run_preview_error(capsys):
    """_run_preview catches exceptions from generate_preview."""
    from deep_earth.cli import _run_preview
    with patch("rasterio.open", side_effect=Exception("corrupt file")):
        _run_preview(
            {"results": {"srtm": "/nonexistent.tif"}},
            "/tmp/out.png",
        )
    # Should not crash — error is logged


def test_cli_run_setup_wizard():
    """run_setup_wizard delegates to setup_wizard function."""
    from deep_earth.cli import run_setup_wizard

    args = MagicMock()
    args.generate_template = True
    args.output = "/tmp/out"

    with patch("deep_earth.setup_wizard.setup_wizard") as mock_sw:
        run_setup_wizard(args)
    mock_sw.assert_called_once_with(
        generate_template=True, output_path="/tmp/out",
    )


def test_cli_main_setup_command():
    """'setup' subcommand dispatches to run_setup_wizard."""
    with patch("deep_earth.cli.run_setup_wizard") as mock_rsw:
        from deep_earth.cli import main
        with patch.object(
            sys, "argv", ["deep_earth", "setup"],
        ):
            main()
        mock_rsw.assert_called_once()


def test_cli_main_no_command(capsys):
    """No subcommand and no --bbox -> prints help."""
    from deep_earth.cli import main
    with patch.object(sys, "argv", ["deep_earth"]):
        main()
    out = capsys.readouterr().out
    assert "usage:" in out.lower() or "Deep Earth" in out
