import os
import pytest
from unittest.mock import patch
from deep_earth.config import Config

def test_default_cache_path():
    with patch.dict(os.environ, {"HOUDINI_USER_PREF_DIR": "/fake/houdini"}):
        config = Config()
        assert config.cache_path == "/fake/houdini/deep_earth_cache"

def test_default_cache_path_no_env():
    with patch.dict(os.environ, {}, clear=True):
        config = Config()
        expected = os.path.join(os.path.expanduser("~/.houdini"), "deep_earth_cache")
        assert config.cache_path == expected

def test_custom_cache_path():
    config = Config(cache_path="/custom/cache")
    assert config.cache_path == "/custom/cache"
