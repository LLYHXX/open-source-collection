from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DeleteAlertMonitorInput(PydanticBaseModel):
    monitor_id: UUID = Field(description="The UUID of the alert monitor to delete")


@register_tool
class DeleteAlertMonitorTool(BaseTool):
    name = "delete_alert_monitor"
    description = (
        "Deletes an alert monitor by ID. This is a soft delete "
        "(marks as deleted, does not permanently remove)."
    )
    category = "tracing"
    input_model = DeleteAlertMonitorInput

    def execute(
        self, params: DeleteAlertMonitorInput, context: ToolContext
    ) -> ToolResult:

        from tracer.models.monitor import UserAlertMonitor

        try:
            monitor = UserAlertMonitor.objects.get(
                id=params.monitor_id, organization=context.organization
            )
        except UserAlertMonitor.DoesNotExist:
            return ToolResult.not_found("Alert Monitor", str(params.monitor_id))

        monitor_name = monitor.name
        monitor_id = str(monitor.id)

        # Soft delete
        monitor.delete()

        info = key_value_block(
            [
                ("Monitor ID", f"`{monitor_id}`"),
                ("Name", monitor_name),
                ("Status", "Deleted"),
            ]
        )

        content = section("Alert Monitor Deleted", info)

        return ToolResult(
            content=content,
            data={
                "monitor_id": monitor_id,
                "name": monitor_name,
                "deleted": True,
            },
        )
