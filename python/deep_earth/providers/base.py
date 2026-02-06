from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

import numpy as np

from deep_earth.region import RegionContext

class DataProviderAdapter(ABC):
    """
    Abstract base class for all geospatial data providers.
    """
    
    @abstractmethod
    async def fetch(self, bbox: Union[RegionContext, Any], resolution: float) -> Any:
        """
        Fetches data for the given bounding box and resolution.

        Args:
            bbox: RegionContext instance or compatible geometry.
            resolution: Requested resolution in meters.

        Returns:
            Provider-specific data (e.g., file path, JSON dict).
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validates the credentials required for this provider.

        Returns:
            True if credentials are valid, False otherwise.
        """
        pass

    @abstractmethod
    def get_cache_key(self, bbox: Union[RegionContext, Any], resolution: float) -> str:
        """
        Generates a unique cache key for the given parameters.

        Args:
            bbox: RegionContext instance or compatible geometry.
            resolution: Requested resolution in meters.

        Returns:
            A unique string hash for caching.
        """
        pass

    @abstractmethod
    def transform_to_grid(self, data: Any, target_grid: Any) -> Union[np.ndarray, Dict[str, np.ndarray]]:
        """
        Transforms the raw fetched data to the target grid format.

        Args:
            data: Raw data as returned by fetch().
            target_grid: The Harmonizer or grid object to align with.

        Returns:
            A NumPy array or a dictionary of arrays.
        """
        pass
