import os
import json
from typing import Optional


class CredentialsManager:
    """
    Manages API credentials for Deep Earth data providers.
    
    Credentials can be provided via:
    1. Direct path to credentials.json
    2. Environment variable DEEP_EARTH_CREDENTIALS_PATH
    3. Default location: $HOUDINI_USER_PREF_DIR/deep_earth/credentials.json
    
    Individual credentials can also be set via environment variables:
    - DEEP_EARTH_GEE_SERVICE_ACCOUNT
    - DEEP_EARTH_GEE_KEY_PATH
    - DEEP_EARTH_OPENTOPO_KEY
    """
    
    def __init__(self, path: Optional[str] = None):
        self.data = {}
        
        # Priority: explicit path > env var > default location
        if path is None:
            path = os.environ.get("DEEP_EARTH_CREDENTIALS_PATH")
        
        if path is None:
            houdini_user_pref = os.environ.get(
                "HOUDINI_USER_PREF_DIR", 
                os.path.expanduser("~/.houdini")
            )
            path = os.path.join(houdini_user_pref, "deep_earth", "credentials.json")
        
        self.path = path
        
        # Load from file if it exists
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                self.data = json.load(f)
    
    def get_ee_service_account(self) -> Optional[str]:
        """Get Earth Engine service account email."""
        env_val = os.environ.get("DEEP_EARTH_GEE_SERVICE_ACCOUNT")
        if env_val:
            return env_val
        return self.data.get("earth_engine", {}).get("service_account")
    
    def get_ee_key_file(self) -> Optional[str]:
        """Get path to Earth Engine service account key file."""
        env_val = os.environ.get("DEEP_EARTH_GEE_KEY_PATH")
        if env_val:
            return env_val
        return self.data.get("earth_engine", {}).get("key_file")
    
    def get_opentopography_key(self) -> Optional[str]:
        """Get OpenTopography API key."""
        env_val = os.environ.get("DEEP_EARTH_OPENTOPO_KEY")
        if env_val:
            return env_val
        return self.data.get("opentopography", {}).get("api_key")
    
    def validate(self) -> dict[str, bool]:
        """Check which credentials are available."""
        return {
            "earth_engine": bool(self.get_ee_service_account() and self.get_ee_key_file()),
            "opentopography": bool(self.get_opentopography_key()),
        }