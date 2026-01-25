"""Server-Sent Events (SSE) formatting utilities"""

import json
from datetime import datetime
from typing import Dict, Any


def convert_datetimes(obj):
    """Recursively convert datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetimes(item) for item in obj]
    return obj


def format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """Format data as SSE event

    Args:
        event_type: Event type (log, data, progress, error, complete)
        data: Event data dictionary

    Returns:
        Formatted SSE event string
    """
    data = convert_datetimes(data)
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
