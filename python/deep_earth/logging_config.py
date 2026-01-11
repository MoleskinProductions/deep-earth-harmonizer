import logging
import os
from typing import Optional, List

def setup_logging(level: Optional[int] = None, log_file: Optional[str] = None) -> None:
    """
    Configures centralized logging for the Deep Earth package.

    Args:
        level: Logging level. If None, checks DEEP_EARTH_LOG_LEVEL then defaults to INFO.
        log_file: Optional path to a log file. Defaults to deep_earth.log in user prefs.
    """
    if level is None:
        env_level = os.environ.get("DEEP_EARTH_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)

    if log_file is None:
        houdini_user_pref = os.environ.get(
            "HOUDINI_USER_PREF_DIR", 
            os.path.expanduser("~/.houdini")
        )
        log_file = os.path.join(houdini_user_pref, "deep_earth.log")

    handlers: List[logging.Handler] = [logging.StreamHandler()]
    
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError:
                pass # Fallback to stream only if dir creation fails
        
        if os.access(log_dir or ".", os.W_OK):
            handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True # Override any existing basicConfig
    )
