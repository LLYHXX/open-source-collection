"""
Temporal logging utilities.

Usage:
    from tfc.logging.temporal import get_logger, bind_context, configure_temporal_logging

    # At worker startup
    configure_temporal_logging()

    # In workflows/activities
    logger = get_logger(__name__)
    bind_context(user_id="123", organization_id="org_456")
    logger.info("event_name", key="value")
"""

from .context import (
    get_temporal_activity_context,
    get_temporal_workflow_context,
    try_activity_info,
    try_workflow_info,
)
from .logger import (
    bind_context,
    clear_context,
    configure_temporal_logging,
    get_logger,
    merge_temporal_context,
)

__all__ = [
    "configure_temporal_logging",
    "get_logger",
    "bind_context",
    "clear_context",
    "merge_temporal_context",
    "get_temporal_activity_context",
    "get_temporal_workflow_context",
    "try_activity_info",
    "try_workflow_info",
]
