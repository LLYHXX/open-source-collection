"""
User & Session Support

Utility module for extracting user and session information from span attributes.
"""

from typing import Any, Dict

import structlog

logger = structlog.get_logger(__name__)


def extract_user_session_info(attributes: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user and session information from span attributes.

    Returns dict with:
    - user_id: User ID if present
    - session_id: Session ID if present
    - user_attributes: Additional user attributes
    """
    from tracer.utils.semantic_conventions import get_attribute

    return {
        "user_id": get_attribute(attributes, "user_id"),
        "session_id": get_attribute(attributes, "session_id"),
        "user_attributes": {
            "email": attributes.get("user.email") or attributes.get("enduser.email"),
            "name": attributes.get("user.name") or attributes.get("enduser.name"),
        },
    }
