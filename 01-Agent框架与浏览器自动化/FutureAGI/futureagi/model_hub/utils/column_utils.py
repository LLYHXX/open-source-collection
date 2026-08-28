"""
Column utilities for data type mapping and response format handling.

This module provides constants and helper functions for determining
column data types based on output format and response format settings.
"""

import uuid
from typing import Any, Optional

# Maps output_format values to column data_type values
OUTPUT_FORMAT_TO_DATA_TYPE = {
    "object": "json",
    "number": "integer",
    "string": "text",
    "array": "array",
    "audio": "audio",
    "image": "image",
}

# Response format types that indicate JSON output
JSON_RESPONSE_FORMAT_TYPES = frozenset({"json_object", "json", "object"})


def _is_uuid(value: Any) -> bool:
    """Check if a value is a UUID or UUID-like string."""
    if isinstance(value, uuid.UUID):
        return True
    if isinstance(value, str):
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False
    return False


def get_response_format_type(response_format: Any) -> Optional[str]:
    """
    Extract the type from a response_format value.

    Args:
        response_format: Can be a dict with 'type' key, a string, a UUID, or None

    Returns:
        The response format type string, or None if not found
    """
    if response_format is None:
        return None

    if isinstance(response_format, dict):
        return response_format.get("type")

    # UUID response_format indicates a custom UserResponseSchema (structured output)
    if _is_uuid(response_format):
        return "json_object"

    if isinstance(response_format, str):
        return response_format

    return None


def is_json_response_format(response_format: Any) -> bool:
    """
    Check if a response format indicates JSON output.

    Args:
        response_format: The response_format value (dict, string, UUID, or None)

    Returns:
        True if the response format indicates JSON output
    """
    response_type = get_response_format_type(response_format)
    if response_type is None:
        return False
    return response_type.lower() in JSON_RESPONSE_FORMAT_TYPES


def get_column_data_type(
    output_format: str,
    response_format: Any = None,
) -> str:
    """
    Determine the column data_type based on output_format and response_format.

    If response_format indicates JSON output (type is json_object, json, or object),
    return "json" data_type to enable proper JSON rendering in the UI.
    Otherwise, use the OUTPUT_FORMAT_TO_DATA_TYPE mapping based on output_format.

    Args:
        output_format: The output_format setting (string, object, etc.)
        response_format: The response_format setting (can be dict or string)

    Returns:
        The appropriate column data_type (json, text, integer, etc.)
    """
    # Check if response_format indicates JSON output
    if is_json_response_format(response_format):
        return "json"

    # Fall back to mapping based on output_format
    return OUTPUT_FORMAT_TO_DATA_TYPE.get(output_format, "text")
