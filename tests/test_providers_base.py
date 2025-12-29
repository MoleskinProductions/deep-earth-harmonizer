import pytest
from deep_earth.providers.base import DataProviderAdapter

def test_base_provider_abstract():
    # Should not be able to instantiate base class
    with pytest.raises(TypeError):
        DataProviderAdapter()

class MockProvider(DataProviderAdapter):
    async def fetch(self, bbox, resolution):
        return "fetched"
    
    def validate_credentials(self):
        return True
    
    def get_cache_key(self, bbox, resolution):
        return "key"
    
    def transform_to_grid(self, data, target_grid):
        return "transformed"

@pytest.mark.asyncio
async def test_mock_provider():
    provider = MockProvider()
    assert await provider.fetch(None, None) == "fetched"
    assert provider.validate_credentials() is True
