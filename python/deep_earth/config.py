import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Config:
    """
    Global configuration manager for the Deep Earth package.
    
    Attributes:
        cache_path (str): The directory used for caching fetched data.
    """
    
    def __init__(self, cache_path: Optional[str] = None):
        """
        Initialize the configuration.

        Args:
            cache_path: Optional custom cache path. If not provided, 
                        defaults to $HOUDINI_USER_PREF_DIR/deep_earth_cache
                        or ~/.houdini/deep_earth_cache.
        """
        if cache_path:
            self.cache_path = cache_path
        else:
            # Default to Houdini user pref dir
            houdini_user_pref = os.environ.get(
                "HOUDINI_USER_PREF_DIR", 
                os.path.expanduser("~/.houdini")
            )
            self.cache_path = os.path.join(houdini_user_pref, "deep_earth_cache")
            
        if not os.path.exists(self.cache_path):
            try:
                os.makedirs(self.cache_path)
            except OSError as e:
                logger.error(f"Failed to create cache directory {self.cache_path}: {e}")
