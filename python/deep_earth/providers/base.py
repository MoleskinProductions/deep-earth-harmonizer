from abc import ABC, abstractmethod

class DataProviderAdapter(ABC):
    @abstractmethod
    async def fetch(self, bbox, resolution):
        """Fetches data for the given bounding box and resolution."""
        pass

    @abstractmethod
    def validate_credentials(self):
        """Validates the credentials required for this provider."""
        pass

    @abstractmethod
    def get_cache_key(self, bbox, resolution):
        """Generates a unique cache key for the given parameters."""
        pass

    @abstractmethod
    def transform_to_grid(self, data, target_grid):
        """Transforms the raw fetched data to the target grid format (NumPy array)."""
        pass
