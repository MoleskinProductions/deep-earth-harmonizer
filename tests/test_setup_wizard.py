"""Tests for setup_wizard.py — interactive and template-based setup.

Covers: get_houdini_packages_dir, generate_package_template,
generate_credentials_template, validate_credential_paths,
setup_wizard, _generate_templates, _interactive_setup.
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from deep_earth.setup_wizard import (
    get_houdini_packages_dir,
    generate_package_template,
    generate_credentials_template,
    validate_credential_paths,
    setup_wizard,
    _generate_templates,
    _interactive_setup,
)


# ---------------------------------------------------------------------------
# get_houdini_packages_dir
# ---------------------------------------------------------------------------

def test_get_houdini_packages_dir_existing(tmp_path):
    """Returns first existing candidate directory."""
    packages = tmp_path / "houdini21.0" / "packages"
    packages.mkdir(parents=True)
    with patch.object(Path, "home", return_value=tmp_path):
        result = get_houdini_packages_dir()
    assert result == packages


def test_get_houdini_packages_dir_env_var(tmp_path):
    """Respects HOUDINI_USER_PREF_DIR environment variable."""
    pref_dir = tmp_path / "houdini_prefs"
    packages = pref_dir / "packages"
    packages.mkdir(parents=True)
    with patch.object(Path, "home", return_value=tmp_path / "nope"), \
         patch.dict(os.environ, {"HOUDINI_USER_PREF_DIR": str(pref_dir)}):
        result = get_houdini_packages_dir()
    assert result == packages


def test_get_houdini_packages_dir_defaults(tmp_path):
    """Falls back to ~/houdini21.0/packages when nothing exists."""
    with patch.object(Path, "home", return_value=tmp_path), \
         patch.dict(os.environ, {}, clear=True):
        # Remove HOUDINI_USER_PREF_DIR if present
        os.environ.pop("HOUDINI_USER_PREF_DIR", None)
        result = get_houdini_packages_dir()
    assert result == tmp_path / "houdini21.0" / "packages"


# ---------------------------------------------------------------------------
# generate_package_template
# ---------------------------------------------------------------------------

def test_generate_package_template():
    """Template contains DEEP_EARTH_ROOT and PYTHONPATH."""
    t = generate_package_template("/opt/deep-earth")
    assert t["env"][0]["DEEP_EARTH_ROOT"] == "/opt/deep-earth"
    assert "$DEEP_EARTH_ROOT/python" in t["env"][1]["PYTHONPATH"]["value"]
    assert t["hpath"] == "$DEEP_EARTH_ROOT"


# ---------------------------------------------------------------------------
# generate_credentials_template
# ---------------------------------------------------------------------------

def test_generate_credentials_template():
    """Template has earth_engine and opentopography sections."""
    t = generate_credentials_template()
    assert "service_account" in t["earth_engine"]
    assert "api_key" in t["opentopography"]


# ---------------------------------------------------------------------------
# validate_credential_paths
# ---------------------------------------------------------------------------

def test_validate_credential_paths_no_env():
    """No env var set -> gee_key_exists is False."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("DEEP_EARTH_GEE_KEY_PATH", None)
        result = validate_credential_paths()
    assert result["gee_key_exists"] is False
    assert result["gee_key_path"] is None


def test_validate_credential_paths_exists(tmp_path):
    """Key file exists -> gee_key_exists is True."""
    key_file = tmp_path / "key.json"
    key_file.write_text("{}")
    with patch.dict(os.environ, {"DEEP_EARTH_GEE_KEY_PATH": str(key_file)}):
        result = validate_credential_paths()
    assert result["gee_key_exists"] is True
    assert result["gee_key_path"] == str(key_file)


def test_validate_credential_paths_missing_file():
    """Key path set but file doesn't exist."""
    with patch.dict(
        os.environ,
        {"DEEP_EARTH_GEE_KEY_PATH": "/nonexistent/key.json"},
    ):
        result = validate_credential_paths()
    assert result["gee_key_exists"] is False
    assert result["gee_key_path"] == "/nonexistent/key.json"


# ---------------------------------------------------------------------------
# setup_wizard dispatch
# ---------------------------------------------------------------------------

def test_setup_wizard_generate_template(tmp_path):
    """generate_template=True delegates to _generate_templates."""
    with patch(
        "deep_earth.setup_wizard._generate_templates"
    ) as mock_gen:
        setup_wizard(generate_template=True, output_path=str(tmp_path))
    mock_gen.assert_called_once()


def test_setup_wizard_interactive():
    """Default mode delegates to _interactive_setup."""
    with patch(
        "deep_earth.setup_wizard._interactive_setup"
    ) as mock_inter:
        setup_wizard(generate_template=False, output_path=None)
    mock_inter.assert_called_once()


# ---------------------------------------------------------------------------
# _generate_templates
# ---------------------------------------------------------------------------

def test_generate_templates_creates_files(tmp_path):
    """Non-interactive mode writes package and creds templates."""
    _generate_templates("/opt/deep-earth", str(tmp_path))

    pkg = tmp_path / "deep_earth.json.template"
    creds = tmp_path / "credentials.json.template"
    assert pkg.exists()
    assert creds.exists()

    pkg_data = json.loads(pkg.read_text())
    assert pkg_data["env"][0]["DEEP_EARTH_ROOT"] == "/opt/deep-earth"

    creds_data = json.loads(creds.read_text())
    assert "earth_engine" in creds_data


def test_generate_templates_creates_output_dir(tmp_path):
    """Output directory is created if it doesn't exist."""
    out = tmp_path / "subdir" / "output"
    _generate_templates("/opt/deep-earth", str(out))
    assert out.exists()
    assert (out / "deep_earth.json.template").exists()


# ---------------------------------------------------------------------------
# _interactive_setup
# ---------------------------------------------------------------------------

def _mock_config(tmp_path):
    """Build a mock Config with a tmp cache path."""
    cfg = MagicMock()
    cfg.cache_path = str(tmp_path / "cache")
    return cfg


def test_interactive_setup_all_creds_ok(tmp_path, capsys):
    """All credentials present -> prints 'All credentials configured!'."""
    mock_creds = MagicMock()
    mock_creds.validate.return_value = {
        "earth_engine": True,
        "opentopography": True,
    }
    with patch("deep_earth.setup_wizard.Config", return_value=_mock_config(tmp_path)), \
         patch("deep_earth.setup_wizard.CredentialsManager", return_value=mock_creds), \
         patch("deep_earth.setup_wizard.validate_credential_paths", return_value={
             "gee_key_path": "/tmp/key.json",
             "gee_key_exists": True,
         }), \
         patch("deep_earth.setup_wizard.get_houdini_packages_dir",
               return_value=tmp_path / "packages"), \
         patch("builtins.input", return_value="n"):
        _interactive_setup("/opt/deep-earth", None)

    out = capsys.readouterr().out
    assert "All credentials configured!" in out
    assert "Earth Engine:   OK" in out
    assert "OpenTopography: OK" in out


def test_interactive_setup_missing_creds(tmp_path, capsys):
    """Missing credentials -> prints 'MISSING' and instructions."""
    mock_creds = MagicMock()
    mock_creds.validate.return_value = {
        "earth_engine": False,
        "opentopography": False,
    }
    with patch("deep_earth.setup_wizard.Config", return_value=_mock_config(tmp_path)), \
         patch("deep_earth.setup_wizard.CredentialsManager", return_value=mock_creds), \
         patch("deep_earth.setup_wizard.validate_credential_paths", return_value={
             "gee_key_path": None,
             "gee_key_exists": False,
         }), \
         patch("deep_earth.setup_wizard.get_houdini_packages_dir",
               return_value=tmp_path / "packages"), \
         patch("builtins.input", return_value="n"):
        _interactive_setup("/opt/deep-earth", None)

    out = capsys.readouterr().out
    assert "MISSING" in out
    assert "DEEP_EARTH_GEE_SERVICE_ACCOUNT" in out
    assert "DEEP_EARTH_OPENTOPO_KEY" in out
    assert "Some credentials are missing" in out


def test_interactive_setup_creates_package_file(tmp_path, capsys):
    """User answers 'y' -> package JSON is created."""
    mock_creds = MagicMock()
    mock_creds.validate.return_value = {
        "earth_engine": True,
        "opentopography": True,
    }
    packages_dir = tmp_path / "packages"
    with patch("deep_earth.setup_wizard.Config", return_value=_mock_config(tmp_path)), \
         patch("deep_earth.setup_wizard.CredentialsManager", return_value=mock_creds), \
         patch("deep_earth.setup_wizard.validate_credential_paths", return_value={
             "gee_key_path": "/tmp/key.json",
             "gee_key_exists": True,
         }), \
         patch("deep_earth.setup_wizard.get_houdini_packages_dir",
               return_value=packages_dir), \
         patch("builtins.input", return_value="y"):
        _interactive_setup("/opt/deep-earth", None)

    pkg_file = packages_dir / "deep_earth.json"
    assert pkg_file.exists()
    data = json.loads(pkg_file.read_text())
    assert data["env"][0]["DEEP_EARTH_ROOT"] == "/opt/deep-earth"


def test_interactive_setup_eof_skips_file(tmp_path, capsys):
    """EOFError (non-interactive) -> skips file creation gracefully."""
    mock_creds = MagicMock()
    mock_creds.validate.return_value = {
        "earth_engine": True,
        "opentopography": True,
    }
    with patch("deep_earth.setup_wizard.Config", return_value=_mock_config(tmp_path)), \
         patch("deep_earth.setup_wizard.CredentialsManager", return_value=mock_creds), \
         patch("deep_earth.setup_wizard.validate_credential_paths", return_value={
             "gee_key_path": "/tmp/key.json",
             "gee_key_exists": True,
         }), \
         patch("deep_earth.setup_wizard.get_houdini_packages_dir",
               return_value=tmp_path / "packages"), \
         patch("builtins.input", side_effect=EOFError):
        _interactive_setup("/opt/deep-earth", None)

    out = capsys.readouterr().out
    assert "Skipped (non-interactive mode)" in out


def test_interactive_setup_key_not_found(tmp_path, capsys):
    """GEE creds present but key file missing -> shows NOT FOUND."""
    mock_creds = MagicMock()
    mock_creds.validate.return_value = {
        "earth_engine": True,
        "opentopography": True,
    }
    with patch("deep_earth.setup_wizard.Config", return_value=_mock_config(tmp_path)), \
         patch("deep_earth.setup_wizard.CredentialsManager", return_value=mock_creds), \
         patch("deep_earth.setup_wizard.validate_credential_paths", return_value={
             "gee_key_path": "/nonexistent/key.json",
             "gee_key_exists": False,
         }), \
         patch("deep_earth.setup_wizard.get_houdini_packages_dir",
               return_value=tmp_path / "packages"), \
         patch("builtins.input", return_value="n"):
        _interactive_setup("/opt/deep-earth", None)

    out = capsys.readouterr().out
    assert "NOT FOUND" in out


def test_interactive_setup_cache_exists(tmp_path, capsys):
    """Cache directory exists -> prints 'exists'."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cfg = MagicMock()
    cfg.cache_path = str(cache_dir)
    mock_creds = MagicMock()
    mock_creds.validate.return_value = {
        "earth_engine": False,
        "opentopography": False,
    }
    with patch("deep_earth.setup_wizard.Config", return_value=cfg), \
         patch("deep_earth.setup_wizard.CredentialsManager", return_value=mock_creds), \
         patch("deep_earth.setup_wizard.validate_credential_paths", return_value={
             "gee_key_path": None,
             "gee_key_exists": False,
         }), \
         patch("deep_earth.setup_wizard.get_houdini_packages_dir",
               return_value=tmp_path / "packages"), \
         patch("builtins.input", return_value="n"):
        _interactive_setup("/opt/deep-earth", None)

    out = capsys.readouterr().out
    assert "exists" in out
