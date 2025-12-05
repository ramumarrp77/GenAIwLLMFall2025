"""Utility functions for Lab 8."""

import json
import logging
from typing import Any

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def format_json(data: Any) -> str:
    """Pretty print JSON data."""
    try:
        if isinstance(data, str):
            data = json.loads(data)
        return json.dumps(data, indent=2)
    except:
        return str(data)

def safe_parse_json(text: str) -> Any:
    """Safely parse JSON with fallback."""
    try:
        return json.loads(text)
    except:
        return text