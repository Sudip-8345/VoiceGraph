"""Simple logging for VoiceBot."""

import logging
import sys

_initialized = False


def setup_logging(level: str = "INFO"):
    """Set up basic logging."""
    global _initialized
    if _initialized:
        return
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    for lib in ["httpx", "httpcore", "whisper", "urllib3"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    _initialized = True


def get_logger(name: str):
    """Get a logger for a module."""
    return logging.getLogger(name)
