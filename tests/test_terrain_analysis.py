import pytest
import numpy as np
from deep_earth.terrain_analysis import (
    compute_slope, 
    compute_aspect, 
    compute_curvature, 
    compute_roughness, 
    compute_tpi,
    compute_twi
)

def test_compute_slope():
    # Create a 45-degree slope
    # cell_size = 1.0
    # dy = 1, dx = 0 -> slope should be 45 degrees
    dem = np.zeros((10, 10))
    for i in range(10):
        dem[i, :] = 10 - i # Height increases as row index decreases (North)
        
    slope = compute_slope(dem, cell_size=1.0)
    
    assert slope.shape == (10, 10)
    # The center values should be 45 degrees
    # Sobel at edges will be different
    assert slope[5, 5] == pytest.approx(45.0, abs=0.5)

def test_compute_aspect():
    dem = np.zeros((10, 10))
    for i in range(10):
        dem[i, :] = 10 - i # Higher in North, sloping South
        
    aspect = compute_aspect(dem, cell_size=1.0)
    
    # Aspect is measured clockwise from North (0°)
    # Sloping South means aspect should be 180°
    # arctan2(-dy, dx)
    # dy = -1 (downwards), dx = 0
    # arctan2(1, 0) = 90 degrees?
    # Wait, let's check the formula in spec: aspect = degrees(arctan2(-dy, dx))
    # If dy is negative (Southward gradient), -dy is positive.
    # arctan2(pos, 0) is 90. 
    # Usually aspect 0 is North, 90 is East, 180 is South, 270 is West.
    # If it slopes South, aspect is 180.
    
    # Let's adjust based on what we expect.
    assert aspect.shape == (10, 10)
    # Sloping South: dy is negative. dx is 0.
    # Let's see what the formula produces.
    expected_aspect = 180.0 
    assert aspect[5, 5] == pytest.approx(expected_aspect, abs=1.0)

def test_compute_curvature():
    # Bowl shape: height = x^2 + y^2. Second derivative is constant 2.
    x, y = np.meshgrid(np.arange(10), np.arange(10))
    dem = (x-5)**2 + (y-5)**2
    
    curv = compute_curvature(dem)
    
    assert curv.shape == (10, 10)
    # Laplace of x^2 + y^2 is 4.
    # Our implementation might scale it differently but it should be positive.
    assert curv[5, 5] > 0

def test_compute_roughness():
    dem = np.zeros((10, 10))
    # Add some noise
    dem[5, 5] = 10.0
    
    rough = compute_roughness(dem, window_size=3)
    
    assert rough.shape == (10, 10)
    assert rough[5, 5] > 0
    assert rough[0, 0] == 0 # Flat areas have 0 roughness

def test_compute_tpi():
    dem = np.zeros((10, 10))
    dem[5, 5] = 10.0 # A peak
    
    tpi = compute_tpi(dem, window_size=3)
    
    assert tpi.shape == (10, 10)
    assert tpi[5, 5] > 0 # Peak should have positive TPI

def test_compute_twi():
    dem = np.zeros((10, 10))
    # Create a valley
    dem[5, 5] = -10.0
    
    twi = compute_twi(dem, cell_size=1.0)
    
    assert twi.shape == (10, 10)
    # TWI should be defined
    assert not np.any(np.isnan(twi))
