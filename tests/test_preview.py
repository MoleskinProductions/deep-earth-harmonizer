import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from deep_earth.preview import generate_preview

def test_preview_elevation():
    """Test generating an elevation preview."""
    dem = np.zeros((10, 10))
    dem[5, 5] = 10.0
    
    with patch("matplotlib.pyplot.imshow") as mock_imshow, \
         patch("matplotlib.pyplot.show") as mock_show, \
         patch("matplotlib.pyplot.colorbar") as mock_colorbar:
        generate_preview(dem, mode="elevation")
        mock_imshow.assert_called_once()
        # Verify that data passed to imshow is the DEM
        args = mock_imshow.call_args[0][0]
        assert np.array_equal(args, dem)

def test_preview_pca():
    """Test generating a PCA embedding preview."""
    embeddings = np.random.rand(64, 10, 10)
    
    with patch("matplotlib.pyplot.imshow") as mock_imshow, \
         patch("matplotlib.pyplot.show") as mock_show:
        generate_preview(embeddings, mode="pca")
        mock_imshow.assert_called_once()
        # Output should be (10, 10, 3)
        args = mock_imshow.call_args[0][0]
        assert args.shape == (10, 10, 3)

def test_preview_biome():
    """Test generating a biome preview."""
    landuse = np.array([["forest", "water"], ["residential", "unknown"]])
    
    with patch("matplotlib.pyplot.imshow") as mock_imshow, \
         patch("matplotlib.pyplot.show") as mock_show:
        generate_preview(landuse, mode="biome")
        mock_imshow.assert_called_once()
        args = mock_imshow.call_args[0][0]
        assert args.shape == (2, 2, 3)

def test_preview_osm():
    """Test generating an OSM overlay preview."""
    data = {
        "elevation": np.zeros((10, 10)),
        "road_distance": np.ones((10, 10)) * 100,
        "water_distance": np.ones((10, 10)) * 100
    }
    
    with patch("matplotlib.pyplot.imshow") as mock_imshow, \
         patch("matplotlib.pyplot.contour") as mock_contour, \
         patch("matplotlib.pyplot.show") as mock_show:
        generate_preview(data, mode="osm")
        mock_imshow.assert_called_once()
        assert mock_contour.call_count == 2

def test_preview_invalid_mode():
    """Test that invalid modes raise an error."""
    with pytest.raises(ValueError):
        generate_preview(np.zeros((10, 10)), mode="invalid")

