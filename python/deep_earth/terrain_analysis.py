import logging
from typing import Any, cast

import numpy as np
from scipy.ndimage import sobel, laplace, uniform_filter, generic_filter

logger = logging.getLogger(__name__)

def compute_slope(dem: np.ndarray, cell_size: float = 10.0) -> np.ndarray:
    """
    Computes the slope (gradient magnitude) in degrees.
    
    Formula:
    dx = sobel(dem, axis=1) / (8 * cell_size)
    dy = sobel(dem, axis=0) / (8 * cell_size)
    slope = degrees(arctan(sqrt(dx**2 + dy**2)))

    Args:
        dem: 2D NumPy array of elevation values.
        cell_size: The distance between pixel centers in meters.

    Returns:
        2D NumPy array of slope values in degrees.
    """
    # Sobel filter in SciPy:
    # axis 1 is along columns (dx)
    # axis 0 is along rows (dy)
    dx = sobel(dem, axis=1) / (8.0 * cell_size)
    dy = sobel(dem, axis=0) / (8.0 * cell_size)
    
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    return cast(np.ndarray, np.degrees(slope_rad))

def compute_aspect(dem: np.ndarray, cell_size: float = 10.0) -> np.ndarray:
    """
    Computes the aspect (gradient direction) in degrees (0-360°).
    0 is North, 90 is East, 180 is South, 270 is West.

    Args:
        dem: 2D NumPy array of elevation values.
        cell_size: The distance between pixel centers in meters.

    Returns:
        2D NumPy array of aspect values in degrees.
    """
    dx = sobel(dem, axis=1) / (8.0 * cell_size)
    dy = sobel(dem, axis=0) / (8.0 * cell_size)
    
    # dz/dx (dx) is positive if height increases East
    # dz/dy (dy) is positive if height increases South
    # Aspect 0 is North (dy > 0), 180 is South (dy < 0)
    # Aspect 90 is East (dx < 0), 270 is West (dx > 0)
    
    # Formula that satisfies this: atan2(-dx, dy)
    aspect_rad = np.arctan2(-dx, dy)
    aspect_deg = np.degrees(aspect_rad)
    
    # Map to 0-360
    aspect_deg = np.mod(aspect_deg + 360, 360)
    
    return cast(np.ndarray, aspect_deg)

def compute_curvature(dem: np.ndarray) -> np.ndarray:
    """
    Computes the profile curvature (second derivative).
    Using the Laplace operator as a proxy for total curvature.

    Args:
        dem: 2D NumPy array of elevation values.

    Returns:
        2D NumPy array of curvature values.
    """
    return cast(np.ndarray, laplace(dem))

def compute_roughness(dem: np.ndarray, window_size: int = 3) -> np.ndarray:
    """
    Computes terrain roughness as the standard deviation within a local window.

    Args:
        dem: 2D NumPy array of elevation values.
        window_size: Size of the neighborhood window (e.g., 3 for 3x3).

    Returns:
        2D NumPy array of roughness values.
    """
    return cast(np.ndarray, generic_filter(dem, np.std, size=window_size))

def compute_tpi(dem: np.ndarray, window_size: int = 3) -> np.ndarray:
    """
    Computes the Topographic Position Index (TPI).
    TPI = elevation - mean_elevation_in_neighborhood

    Args:
        dem: 2D NumPy array of elevation values.
        window_size: Size of the neighborhood window.

    Returns:
        2D NumPy array of TPI values.
    """
    mean_dem = uniform_filter(dem, size=window_size)
    return cast(np.ndarray, dem - mean_dem)

def compute_twi(dem: np.ndarray, cell_size: float = 10.0) -> np.ndarray:
    """
    Computes a simplified Topographic Wetness Index (TWI).
    Note: A true TWI requires flow accumulation. This version uses a proxy.

    Args:
        dem: 2D NumPy array of elevation values.
        cell_size: Meter-resolution of cells.

    Returns:
        2D NumPy array of TWI values.
    """
    slope = compute_slope(dem, cell_size)
    # tan(slope)
    tan_beta = np.tan(np.radians(slope))
    tan_beta = np.where(tan_beta <= 0, 0.001, tan_beta) # Avoid division by zero
    
    # Simple proxy for alpha (contributing area): using TPI as a local catchment proxy
    # In reality, this is not accurate, but serves as a placeholder for the spec.
    alpha = np.maximum(1.0, compute_tpi(dem, window_size=5) + 1.0)
    
    return np.log(alpha / tan_beta)
