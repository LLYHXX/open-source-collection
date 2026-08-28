"""
Temporal context extraction helpers.
"""

import temporalio.activity
import temporalio.workflow


def try_activity_info():
    """Safely get activity info, returns None if not in activity."""
    try:
        return temporalio.activity.info()
    except RuntimeError:
        return None


def try_workflow_info():
    """Safely get workflow info, returns None if not in workflow."""
    try:
        return temporalio.workflow.info()
    except RuntimeError:
        return None


def get_temporal_activity_context() -> dict:
    """
    Get context dict from current activity.

    Returns activity metadata that will be added to all logs
    within the activity execution.
    """
    info = try_activity_info()
    if info is None:
        return {}

    return {
        "activity_id": info.activity_id,
        "activity_type": info.activity_type,
        "attempt": info.attempt,
        "task_queue": info.task_queue,
        "workflow_id": info.workflow_id,
        "workflow_namespace": info.workflow_namespace,
        "workflow_run_id": info.workflow_run_id,
        "workflow_type": info.workflow_type,
    }


def get_temporal_workflow_context() -> dict:
    """
    Get context dict from current workflow.

    Returns workflow metadata that will be added to all logs
    within the workflow execution.
    """
    info = try_workflow_info()
    if info is None:
        return {}

    return {
        "attempt": info.attempt,
        "task_queue": info.task_queue,
        "workflow_id": info.workflow_id,
        "workflow_namespace": info.namespace,
        "workflow_run_id": info.run_id,
        "workflow_type": info.workflow_type,
    }
