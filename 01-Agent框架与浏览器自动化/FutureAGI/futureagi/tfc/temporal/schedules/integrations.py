"""
Integration Temporal schedules.

These define periodic tasks for syncing external platform data.
"""

from typing import List

from tfc.temporal.schedules.config import ScheduleConfig

INTEGRATION_SCHEDULES: List[ScheduleConfig] = [
    ScheduleConfig(
        schedule_id="sync-integrations",
        activity_name="poll_active_integrations",
        interval_seconds=60,
        queue="tasks_s",
        description="Poll active integration connections and dispatch sync activities",
    ),
    ScheduleConfig(
        schedule_id="check-integration-errors",
        activity_name="check_integration_error_alerts",
        interval_seconds=900,  # 15 minutes
        queue="tasks_s",
        description="Send email alerts for connections in error state > 1 hour",
    ),
]
