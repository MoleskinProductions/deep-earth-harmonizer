import os
import json

class CredentialsManager:
    def __init__(self, path=None):
        if path is None:
            # Default location based on Houdini user pref dir (mocking for non-houdini env)
            houdini_user_pref = os.environ.get("HOUDINI_USER_PREF_DIR", os.path.expanduser("~/.houdini"))
            path = os.path.join(houdini_user_pref, "deep_earth", "credentials.json")
        
        self.path = path
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Credentials file not found at {self.path}")
        
        with open(self.path, "r") as f:
            self.data = json.load(f)
            
    def get_ee_service_account(self):
        return self.data.get("earth_engine", {}).get("service_account")
        
    def get_ee_key_file(self):
        return self.data.get("earth_engine", {}).get("key_file")
        
    def get_opentopography_key(self):
        return self.data.get("opentopography", {}).get("api_key")
