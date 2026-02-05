"""
Deep Earth Harmonizer - Setup Wizard
Helps configure credentials and environment for studio deployment.
"""

import os
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from deep_earth.credentials import CredentialsManager
from deep_earth.config import Config


def get_houdini_packages_dir() -> Path:
    """Find the Houdini packages directory."""
    # Check common locations
    home = Path.home()
    candidates = [
        home / "houdini21.0" / "packages",
        home / "houdini20.5" / "packages",
        home / "houdini20.0" / "packages",
        Path(os.environ.get("HOUDINI_USER_PREF_DIR", "")) / "packages",
    ]

    for path in candidates:
        if path.exists():
            return path

    # Default to 21.0
    return home / "houdini21.0" / "packages"


def generate_package_template(project_root: str) -> dict:
    """Generate a Houdini package JSON template using environment variables."""
    return {
        "env": [
            {
                "DEEP_EARTH_ROOT": project_root
            },
            {
                "PYTHONPATH": {
                    "value": ["$DEEP_EARTH_ROOT/python"],
                    "method": "prepend"
                }
            }
        ],
        "hpath": "$DEEP_EARTH_ROOT"
    }


def generate_credentials_template() -> dict:
    """Generate a credentials JSON template."""
    return {
        "earth_engine": {
            "service_account": "YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com",
            "key_file": "/path/to/your/service-account-key.json"
        },
        "opentopography": {
            "api_key": "YOUR_OPENTOPOGRAPHY_API_KEY"
        }
    }


def validate_credential_paths() -> dict:
    """Check if credential files exist."""
    results: Dict[str, Any] = {
        "gee_key_exists": False,
        "gee_key_path": None,
    }

    key_path = os.environ.get("DEEP_EARTH_GEE_KEY_PATH")
    if key_path:
        results["gee_key_path"] = key_path
        results["gee_key_exists"] = os.path.isfile(key_path)

    return results


def setup_wizard(generate_template: bool = False, output_path: Optional[str] = None) -> None:
    """
    Run the setup wizard.

    Args:
        generate_template: If True, generate template files without prompts.
        output_path: Optional path for generated files.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    if generate_template:
        _generate_templates(project_root, output_path)
        return

    _interactive_setup(project_root, output_path)


def _generate_templates(project_root: str, output_path: Optional[str]) -> None:
    """Generate template files non-interactively."""
    output_dir = Path(output_path) if output_path else Path(project_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate package template
    package_json = generate_package_template(project_root)
    package_path = output_dir / "deep_earth.json.template"
    with open(package_path, "w") as f:
        json.dump(package_json, f, indent=4)
    print(f"Generated: {package_path}")

    # Generate credentials template
    creds_json = generate_credentials_template()
    creds_path = output_dir / "credentials.json.template"
    with open(creds_path, "w") as f:
        json.dump(creds_json, f, indent=4)
    print(f"Generated: {creds_path}")

    print("\nTemplates generated. Edit these files with your paths and credentials.")


def _interactive_setup(project_root: str, output_path: Optional[str]) -> None:
    """Run the interactive setup wizard."""
    print("=" * 50)
    print("  Deep Earth Harmonizer - Setup Wizard")
    print("=" * 50)

    config = Config()
    creds = CredentialsManager()

    # Step 1: Check credentials
    print("\n[1/4] Checking Credentials...")
    print("-" * 40)
    status = creds.validate()
    cred_paths = validate_credential_paths()

    print(f"  Earth Engine:   {'OK' if status['earth_engine'] else 'MISSING'}")
    if not status['earth_engine']:
        print("    Set: DEEP_EARTH_GEE_SERVICE_ACCOUNT")
        print("    Set: DEEP_EARTH_GEE_KEY_PATH")
    elif cred_paths["gee_key_path"]:
        key_exists = "exists" if cred_paths["gee_key_exists"] else "NOT FOUND"
        print(f"    Key file: {cred_paths['gee_key_path']} ({key_exists})")

    print(f"  OpenTopography: {'OK' if status['opentopography'] else 'MISSING'}")
    if not status['opentopography']:
        print("    Set: DEEP_EARTH_OPENTOPO_KEY")

    # Step 2: Cache configuration
    print("\n[2/4] Cache Configuration")
    print("-" * 40)
    print(f"  Cache path: {config.cache_path}")
    cache_exists = os.path.isdir(config.cache_path)
    print(f"  Status: {'exists' if cache_exists else 'will be created on first use'}")

    # Step 3: Houdini package configuration
    print("\n[3/4] Houdini Package Configuration")
    print("-" * 40)
    packages_dir = get_houdini_packages_dir()
    print(f"  Detected packages dir: {packages_dir}")

    package_json = generate_package_template(project_root)

    print("\n  Recommended deep_earth.json:")
    print("  " + json.dumps(package_json, indent=4).replace("\n", "\n  "))

    # Ask to create the file
    print()
    try:
        response = input(f"  Create {packages_dir}/deep_earth.json? [y/N]: ").strip().lower()
        if response == 'y':
            packages_dir.mkdir(parents=True, exist_ok=True)
            package_file = packages_dir / "deep_earth.json"
            with open(package_file, "w") as f:
                json.dump(package_json, f, indent=4)
            print(f"  Created: {package_file}")
        else:
            print("  Skipped. You can create the file manually.")
    except (EOFError, KeyboardInterrupt):
        print("\n  Skipped (non-interactive mode).")

    # Step 4: Summary
    print("\n[4/4] Summary")
    print("-" * 40)
    all_ok = status['earth_engine'] and status['opentopography']

    if all_ok:
        print("  All credentials configured!")
        print("  You can now use Deep Earth in Houdini.")
    else:
        print("  Some credentials are missing.")
        print("  See docs/CREDENTIALS.md for setup instructions.")

    print("\n  Next steps:")
    print("    1. Set missing environment variables (if any)")
    print("    2. Restart Houdini to load the package")
    print("    3. Create a 'Deep Earth Harmonizer' node")
    print()
