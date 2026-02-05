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


def test_setup_logging_nonexistent_log_dir(tmp_path):
    """Log dir doesn't exist -> created automatically."""
    from deep_earth.logging_config import setup_logging

    log_file = str(tmp_path / "new_subdir" / "deep_earth.log")
    with patch('logging.basicConfig'):
        setup_logging(log_file=log_file)
    assert os.path.isdir(str(tmp_path / "new_subdir"))


def test_setup_logging_unwritable_dir(tmp_path):
    """Unwritable log dir -> falls back to stream handler only."""
    from deep_earth.logging_config import setup_logging

    bad_dir = tmp_path / "readonly"
    bad_dir.mkdir()
    os.chmod(str(bad_dir), 0o444)
    log_file = str(bad_dir / "deep_earth.log")
    try:
        with patch('logging.basicConfig') as mock_bc:
            setup_logging(log_file=log_file)
            _, kwargs = mock_bc.call_args
            handlers = kwargs['handlers']
            # Should only have StreamHandler (no FileHandler)
            assert all(
                isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
                for h in handlers
            )
    finally:
        os.chmod(str(bad_dir), 0o755)
