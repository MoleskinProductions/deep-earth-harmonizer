import pytest
import numpy as np
from deep_earth.houdini.visualization import compute_pca_colors, apply_biome_colors

def test_compute_pca_colors():
    # Create some dummy embeddings (N=100, D=64)
    # We'll make them distinct so PCA has something to find
    embeddings = np.random.rand(100, 64)
    
    colors = compute_pca_colors(embeddings)
    
    assert colors.shape == (100, 3)
    assert np.all(colors >= 0.0)
    assert np.all(colors <= 1.0)
    
    # Check with (D, H, W) shape
    embeddings_grid = np.random.rand(64, 10, 10)
    colors_grid = compute_pca_colors(embeddings_grid)
    assert colors_grid.shape == (100, 3)

def test_apply_biome_colors():
    landuse = np.array(["forest", "water", "residential", "unknown"])
    colors = apply_biome_colors(landuse)
    
    assert colors.shape == (4, 3)
    # Forest should be green
    assert np.allclose(colors[0], [0.1, 0.5, 0.1])
    # Water should be blue
    assert np.allclose(colors[1], [0.1, 0.3, 0.8])
    # Residential should be grey
    assert np.allclose(colors[2], [0.5, 0.5, 0.5])
    # Unknown should be default grey
    assert np.allclose(colors[3], [0.5, 0.5, 0.5])
