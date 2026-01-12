"""
Deep Earth Harmonizer - Setup Wizard
Helps configure credentials and environment for studio deployment.
"""

import os
import json
import sys
import logging
from deep_earth.credentials import CredentialsManager
from deep_earth.config import Config

def setup_wizard():
    print("=== Deep Earth Harmonizer Setup Wizard ===")
    
    config = Config()
    creds = CredentialsManager()
    
    print(f"\n1. Cache Configuration")
    print(f"Current Cache Path: {config.cache_path}")
    
    print(f"\n2. Credential Status")
    status = creds.validate()
    
    print(f"  Earth Engine: {'VALID' if status['earth_engine'] else 'MISSING'}")
    if not status['earth_engine']:
        print("    Requires: DEEP_EARTH_GEE_SERVICE_ACCOUNT & DEEP_EARTH_GEE_KEY_PATH")
        
    print(f"  OpenTopography: {'VALID' if status['opentopography'] else 'MISSING'}")
    if not status['opentopography']:
        print("    Requires: DEEP_EARTH_OPENTOPO_KEY")

    print("\n3. Houdini Package Configuration")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    package_json = {
        "hpath": project_root,
        "env": [
            {
                "PYTHONPATH": [
                    os.path.join(project_root, "python"),
                    os.path.join(project_root, "venv_houdini/lib/python3.11/site-packages")
                ]
            }
        ]
    }
    
    print("\nRecommended planet_embeddings.json for ~/houdini21.0/packages/:")
    print(json.dumps(package_json, indent=4))
    
    print("\nSetup complete. Ensure your environment variables are set in your shell or the package JSON.")

if __name__ == "__main__":
    setup_wizard()
