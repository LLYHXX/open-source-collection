"""
Backwards compatibility helpers.

Provides deprecated functions that map to the new API.
"""

import warnings
from typing import Callable, List, Tuple, Type

from tfc.temporal.common.client import get_client_sync
from tfc.temporal.common.registry import (
    get_activities_for_queue,
    get_workflows_for_queue,
)


def get_temporal_client():
    """
    DEPRECATED: Use get_client() instead.

    This is kept for backwards compatibility.
    """
    warnings.warn(
        "get_temporal_client() is deprecated, use get_client() from tfc.temporal instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_client_sync()


def get_workflows_and_activities_for_queue(
    task_queue: str,
) -> Tuple[List[Type], List[Callable]]:
    """
    DEPRECATED: Use get_workflows_for_queue() and get_activities_for_queue() instead.

    This is kept for backwards compatibility with the management command.
    """
    workflows = get_workflows_for_queue(task_queue)
    activities = get_activities_for_queue(task_queue)
    return workflows, activities


__all__ = [
    "get_temporal_client",
    "get_workflows_and_activities_for_queue",
]
