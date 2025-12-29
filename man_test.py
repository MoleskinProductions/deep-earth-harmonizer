from deep_earth.credentials import CredentialsManager
from deep_earth.config import Config
 
config = Config()
print(f"Cache Path: {config.cache_path}")
 
try:
    creds = CredentialsManager()
    print(f"EE Service Account: {creds.get_ee_service_account()}")
    print(f"OT API Key: {creds.get_opentopography_key()}")
except FileNotFoundError as e:
    print(f"Verification Info: {e}")
    print("Please create the credentials file to fully verify.")
