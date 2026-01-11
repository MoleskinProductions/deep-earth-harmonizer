import os
import json
from typing import Optional, Dict, Any, cast


class CredentialsManager:
    """
    Manages API credentials for Deep Earth data providers.
    
    Priority for loading credentials:
    1. Direct path provided to constructor.
    2. Environment variable `DEEP_EARTH_CREDENTIALS_PATH`.
    3. Default location: `$HOUDINI_USER_PREF_DIR/deep_earth/credentials.json`.
    
    Attributes:
        path (str): The resolved path to the credentials file.
        data (Dict[str, Any]): The loaded credential data.
    """
    
    def __init__(self, path: Optional[str] = None):
        """
        Initialize the CredentialsManager.

        Args:
            path: Optional direct path to a credentials.json file.
        """
        self.data: Dict[str, Any] = {}
        
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
            try:
                with open(self.path, "r") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
    
    def get_ee_service_account(self) -> Optional[str]:
        """
        Get Earth Engine service account email.

        Returns:
            The service account email if found, None otherwise.
        """
        env_val = os.environ.get("DEEP_EARTH_GEE_SERVICE_ACCOUNT")
        if env_val:
            return env_val
        return cast(Optional[str], self.data.get("earth_engine", {}).get("service_account"))
    
    def get_ee_key_file(self) -> Optional[str]:
        """
        Get path to Earth Engine service account key file.

        Returns:
            The absolute path to the key file if found, None otherwise.
        """
        env_val = os.environ.get("DEEP_EARTH_GEE_KEY_PATH")
        if env_val:
            return env_val
        return cast(Optional[str], self.data.get("earth_engine", {}).get("key_file"))
    
    def get_opentopography_key(self) -> Optional[str]:
        """
        Get OpenTopography API key.

        Returns:
            The API key if found, None otherwise.
        """
        env_val = os.environ.get("DEEP_EARTH_OPENTOPO_KEY")
        if env_val:
            return env_val
        return cast(Optional[str], self.data.get("opentopography", {}).get("api_key"))
    
    def validate(self) -> Dict[str, bool]:
        """
        Check which credentials are available and valid.

        Returns:
            A dictionary mapping provider names to boolean validity status.
        """
        return {
            "earth_engine": bool(self.get_ee_service_account() and self.get_ee_key_file()),
            "opentopography": bool(self.get_opentopography_key()),
        }