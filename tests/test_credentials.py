import os
import json
import pytest
from unittest.mock import patch, mock_open
from deep_earth.credentials import CredentialsManager

@pytest.fixture
def mock_credentials():
    return {
        "earth_engine": {
            "service_account": "test@appspot.gserviceaccount.com",
            "key_file": "/tmp/key.json"
        },
        "opentopography": {
            "api_key": "test_api_key"
        }
    }

def test_load_credentials(mock_credentials):
    mock_data = json.dumps(mock_credentials)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("os.path.exists", return_value=True):
            manager = CredentialsManager(path="/dummy/path/credentials.json")
            assert manager.get_ee_service_account() == "test@appspot.gserviceaccount.com"
            assert manager.get_ee_key_file() == "/tmp/key.json"
            assert manager.get_opentopography_key() == "test_api_key"

def test_missing_file():
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            CredentialsManager(path="/non/existent/path.json")

def test_default_path(mock_credentials):
    mock_data = json.dumps(mock_credentials)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("os.path.exists", return_value=True):
            with patch.dict(os.environ, {"HOUDINI_USER_PREF_DIR": "/fake/houdini"}):
                manager = CredentialsManager()
                assert manager.path == "/fake/houdini/deep_earth/credentials.json"

def test_default_path_no_env(mock_credentials):
    mock_data = json.dumps(mock_credentials)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("os.path.exists", return_value=True):
            with patch.dict(os.environ, {}, clear=True):
                manager = CredentialsManager()
                expected = os.path.join(os.path.expanduser("~/.houdini"), "deep_earth", "credentials.json")
                assert manager.path == expected