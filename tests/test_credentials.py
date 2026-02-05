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


def test_load_credentials_from_file(mock_credentials):
    """Test loading credentials from a JSON file."""
    mock_data = json.dumps(mock_credentials)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("os.path.exists", return_value=True):
            manager = CredentialsManager(path="/dummy/path/credentials.json")
            assert manager.get_ee_service_account() == "test@appspot.gserviceaccount.com"
            assert manager.get_ee_key_file() == "/tmp/key.json"
            assert manager.get_opentopography_key() == "test_api_key"


def test_missing_file_does_not_raise():
    """Missing file should not raise - credentials may come from env vars."""
    with patch("os.path.exists", return_value=False):
        manager = CredentialsManager(path="/non/existent/path.json")
        assert manager.data == {}
        assert manager.get_ee_service_account() is None


def test_env_var_precedence(mock_credentials):
    """Environment variables should take precedence over file values."""
    mock_data = json.dumps(mock_credentials)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("os.path.exists", return_value=True):
            with patch.dict(os.environ, {
                "DEEP_EARTH_GEE_SERVICE_ACCOUNT": "env@example.com",
                "DEEP_EARTH_OPENTOPO_KEY": "env_key"
            }):
                manager = CredentialsManager(path="/dummy/path/credentials.json")
                # Env vars should win
                assert manager.get_ee_service_account() == "env@example.com"
                assert manager.get_opentopography_key() == "env_key"
                # File value used when no env var
                assert manager.get_ee_key_file() == "/tmp/key.json"


def test_credentials_path_env_var(mock_credentials):
    """DEEP_EARTH_CREDENTIALS_PATH should override default path."""
    mock_data = json.dumps(mock_credentials)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("os.path.exists", return_value=True):
            with patch.dict(os.environ, {"DEEP_EARTH_CREDENTIALS_PATH": "/custom/creds.json"}, clear=False):
                manager = CredentialsManager()
                assert manager.path == "/custom/creds.json"


def test_default_path():
    """Default path should use HOUDINI_USER_PREF_DIR."""
    with patch("os.path.exists", return_value=False):
        with patch.dict(os.environ, {"HOUDINI_USER_PREF_DIR": "/fake/houdini"}, clear=False):
            # Clear the credentials path env var if set
            env = os.environ.copy()
            env.pop("DEEP_EARTH_CREDENTIALS_PATH", None)
            with patch.dict(os.environ, env, clear=True):
                with patch.dict(os.environ, {"HOUDINI_USER_PREF_DIR": "/fake/houdini"}):
                    manager = CredentialsManager()
                    assert manager.path == "/fake/houdini/deep_earth/credentials.json"


def test_validate_method(mock_credentials):
    """Test the validate() method returns correct status."""
    mock_data = json.dumps(mock_credentials)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("os.path.exists", return_value=True):
            manager = CredentialsManager(path="/dummy/path/credentials.json")
            validation = manager.validate()
            assert validation["earth_engine"] is True
            assert validation["opentopography"] is True


def test_validate_partial():
    """Test validate() with partial credentials."""
    partial_creds = {"opentopography": {"api_key": "key"}}
    mock_data = json.dumps(partial_creds)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("os.path.exists", return_value=True):
            manager = CredentialsManager(path="/dummy.json")
            validation = manager.validate()
            assert validation["earth_engine"] is False
            assert validation["opentopography"] is True


def test_corrupt_json_file():
    """Corrupt JSON file -> data stays empty, no exception."""
    with patch("builtins.open", mock_open(read_data="{bad json!!")):
        with patch("os.path.exists", return_value=True):
            manager = CredentialsManager(path="/corrupt.json")
    assert manager.data == {}


def test_get_ee_key_file_from_env():
    """DEEP_EARTH_GEE_KEY_PATH env var returns key file path."""
    with patch("os.path.exists", return_value=False):
        manager = CredentialsManager(path="/x.json")
    with patch.dict(os.environ, {"DEEP_EARTH_GEE_KEY_PATH": "/my/key.json"}):
        assert manager.get_ee_key_file() == "/my/key.json"


def test_get_gcs_bucket_from_env():
    """DEEP_EARTH_GCS_BUCKET env var returns bucket name."""
    with patch("os.path.exists", return_value=False):
        manager = CredentialsManager(path="/x.json")
    with patch.dict(os.environ, {"DEEP_EARTH_GCS_BUCKET": "my-bucket"}):
        assert manager.get_gcs_bucket() == "my-bucket"


def test_get_gcs_bucket_from_file():
    """GCS bucket loaded from credentials file."""
    creds = {
        "earth_engine": {"gcs_bucket": "file-bucket"},
    }
    mock_data = json.dumps(creds)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("os.path.exists", return_value=True):
            manager = CredentialsManager(path="/dummy.json")
    # No env var set
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("DEEP_EARTH_GCS_BUCKET", None)
        assert manager.get_gcs_bucket() == "file-bucket"


def test_get_gcs_bucket_none():
    """No bucket configured -> returns None."""
    with patch("os.path.exists", return_value=False):
        manager = CredentialsManager(path="/x.json")
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("DEEP_EARTH_GCS_BUCKET", None)
        assert manager.get_gcs_bucket() is None