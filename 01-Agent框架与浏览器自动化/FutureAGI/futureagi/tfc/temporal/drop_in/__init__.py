"""
Drop-in replacement for Celery tasks using Temporal.

This module provides decorators and utilities that mimic Celery's interface
while using Temporal under the hood.

Usage:
    # Replace @celery_app.task with @temporal_activity
    from tfc.temporal.drop_in import temporal_activity

    @temporal_activity(time_limit=3600, queue="tasks_l")
    def my_task(arg1, arg2):
        # Your existing sync code - no changes needed
        ...

    # Call the task (works like Celery!)
    my_task.apply_async(args=(arg1, arg2))
    my_task.delay(arg1, arg2)

    # Or use start_activity directly
    from tfc.temporal.drop_in import start_activity
    start_activity("my_task", args=(arg1, arg2), queue="tasks_l")
"""

# Decorator functions
from tfc.temporal.drop_in.decorator import (
    get_activity_by_name,
    get_all_activity_functions,
    get_temporal_activities,
    temporal_activity,
)

# Runner functions
from tfc.temporal.drop_in.runner import (
    start_activity,
    start_activity_async,
    start_activity_sync,
)

# Workflow types
from tfc.temporal.drop_in.workflow import (
    TaskRunnerInput,
    TaskRunnerOutput,
    TaskRunnerWorkflow,
)


def get_drop_in_workflows():
    """Get all workflows for worker registration."""
    return [TaskRunnerWorkflow]


def get_drop_in_activities():
    """
    Get all registered activities for worker registration.

    Note: This should be called AFTER all modules with @temporal_activity
    decorators have been imported.
    """
    return get_temporal_activities()


__all__ = [
    # Decorator
    "temporal_activity",
    # Runner helpers
    "start_activity",
    "start_activity_sync",
    "start_activity_async",
    # Workflow types
    "TaskRunnerInput",
    "TaskRunnerOutput",
    "TaskRunnerWorkflow",
    # Registration helpers
    "get_drop_in_workflows",
    "get_drop_in_activities",
    "get_activity_by_name",
    "get_all_activity_functions",
    "get_temporal_activities",
]
