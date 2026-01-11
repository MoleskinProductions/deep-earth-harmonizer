import os

class Config:
    def __init__(self, cache_path=None):
        if cache_path is None:
            houdini_user_pref = os.environ.get("HOUDINI_USER_PREF_DIR", os.path.expanduser("~/.houdini"))
            cache_path = os.path.join(houdini_user_pref, "deep_earth_cache")
        
        self.cache_path = cache_path
