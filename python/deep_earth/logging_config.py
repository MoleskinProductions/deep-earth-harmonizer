import logging
import os

def setup_logging():
    level_name = os.environ.get("DEEP_EARTH_LOG_LEVEL", "INFO")
    # Get level from logging module, default to INFO if invalid
    level = getattr(logging, level_name.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("deep_earth.log")
        ]
    )
