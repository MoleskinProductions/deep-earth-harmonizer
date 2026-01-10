import os
import logging
import pytest
from unittest.mock import patch
import sys

# Ensure we can import the module (even if it doesn't exist yet, pytest collects it)
# We expect ImportError during test execution or collection if the module is missing
try:
    from deep_earth.logging_config import setup_logging
except ImportError:
    pass

def test_setup_logging_defaults():
    # We need to ensure the module is importable for this test to actually run logic
    # But for TDD "Red" phase, failing on Import is acceptable.
    from deep_earth.logging_config import setup_logging
    
    with patch('logging.basicConfig') as mock_basic_config:
        setup_logging()
        
        # Verify call args
        args, kwargs = mock_basic_config.call_args
        assert kwargs['level'] == logging.INFO
        
        handlers = kwargs['handlers']
        assert len(handlers) == 2
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)
        assert any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith("deep_earth.log") for h in handlers)

def test_setup_logging_env_var():
    from deep_earth.logging_config import setup_logging
    
    with patch.dict(os.environ, {"DEEP_EARTH_LOG_LEVEL": "DEBUG"}):
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging()
            args, kwargs = mock_basic_config.call_args
            assert kwargs['level'] == logging.DEBUG
