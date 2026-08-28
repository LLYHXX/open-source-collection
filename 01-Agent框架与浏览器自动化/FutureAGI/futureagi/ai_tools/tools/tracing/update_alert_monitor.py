from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class UpdateAlertMonitorInput(PydanticBaseModel):
    monitor_id: UUID = Field(description="The UUID of the alert monitor to update")
    name: Optional[str] = Field(default=None, description="Updated monitor name")
    critical_threshold_value: Optional[float] = Field(
        default=None, description="Updated critical threshold value"
    )
    warning_threshold_value: Optional[float] = Field(
        default=None, description="Updated warning threshold value"
    )
    is_mute: Optional[bool] = Field(
        default=None, description="Whether the monitor is muted (paused)"
    )
    alert_frequency: Optional[int] = Field(
        default=None, ge=5, description="Updated alert check frequency in minutes"
    )
    notification_emails: Optional[list[str]] = Field(
        default=None, description="Updated list of notification email addresses"
    )


@register_tool
class UpdateAlertMonitorTool(BaseTool):
    name = "update_alert_monitor"
    description = (
        "Updates an existing alert monitor's configuration, including name, "
        "thresholds, mute status, frequency, and notification emails."
    )
    category = "tracing"
    input_model = UpdateAlertMonitorInput

    def execute(
        self, params: UpdateAlertMonitorInput, context: ToolContext
    ) -> ToolResult:

        from tracer.models.monitor import (
            ThresholdCalculationMethodChoices,
            UserAlertMonitor,
        )

        try:
            monitor = UserAlertMonitor.objects.select_related("project").get(
                id=params.monitor_id, organization=context.organization
            )
        except UserAlertMonitor.DoesNotExist:
            return ToolResult.not_found("Alert Monitor", str(params.monitor_id))

        # Validate max 5 notification emails
        if (
            params.notification_emails is not None
            and len(params.notification_emails) > 5
        ):
            return ToolResult.error(
                "You can specify at most 5 notification emails.",
                error_code="VALIDATION_ERROR",
            )

        # Validate unique name per project (excluding current instance)
        if params.name is not None and monitor.project:
            if (
                UserAlertMonitor.objects.filter(
                    project=monitor.project, name=params.name
                )
                .exclude(pk=monitor.pk)
                .exists()
            ):
                return ToolResult.error(
                    f"An alert with the name '{params.name}' already exists in this project.",
                    error_code="VALIDATION_ERROR",
                )

        changes = []

        if params.name is not None:
            old = monitor.name
            monitor.name = params.name
            changes.append(f"name: '{old}' -> '{params.name}'")

        if params.critical_threshold_value is not None:
            old = monitor.critical_threshold_value
            monitor.critical_threshold_value = params.critical_threshold_value
            changes.append(
                f"critical_threshold: {old} -> {params.critical_threshold_value}"
            )

        if params.warning_threshold_value is not None:
            old = monitor.warning_threshold_value
            monitor.warning_threshold_value = params.warning_threshold_value
            changes.append(
                f"warning_threshold: {old} -> {params.warning_threshold_value}"
            )

        if params.is_mute is not None:
            old = monitor.is_mute
            monitor.is_mute = params.is_mute
            changes.append(f"is_mute: {old} -> {params.is_mute}")

        if params.alert_frequency is not None:
            old = monitor.alert_frequency
            monitor.alert_frequency = params.alert_frequency
            changes.append(f"alert_frequency: {old} -> {params.alert_frequency}")

        if params.notification_emails is not None:
            old = monitor.notification_emails
            monitor.notification_emails = params.notification_emails
            changes.append(
                f"notification_emails updated ({len(params.notification_emails)} emails)"
            )

        if not changes:
            return ToolResult.error(
                "No changes provided. Specify at least one field to update.",
                error_code="VALIDATION_ERROR",
            )

        # Validate threshold relationships using merged values
        effective_critical = monitor.critical_threshold_value
        effective_warning = monitor.warning_threshold_value
        effective_threshold_type = monitor.threshold_type
        effective_operator = monitor.threshold_operator

        if effective_threshold_type in [
            ThresholdCalculationMethodChoices.PERCENTAGE_CHANGE.value,
            ThresholdCalculationMethodChoices.STATIC.value,
        ]:
            if effective_critical is None:
                return ToolResult.error(
                    "Critical threshold is required for percentage change and static threshold.",
                    error_code="VALIDATION_ERROR",
                )
            if (
                effective_operator in ["greater_than", "less_than"]
                and effective_warning is not None
            ):
                if effective_operator == "greater_than" and not (
                    effective_critical > effective_warning
                ):
                    return ToolResult.error(
                        "Critical threshold must be greater than warning threshold for 'greater_than' operator.",
                        error_code="VALIDATION_ERROR",
                    )
                if effective_operator == "less_than" and not (
                    effective_critical < effective_warning
                ):
                    return ToolResult.error(
                        "Critical threshold must be less than warning threshold for 'less_than' operator.",
                        error_code="VALIDATION_ERROR",
                    )

        monitor.save()

        info = key_value_block(
            [
                ("Monitor ID", f"`{monitor.id}`"),
                ("Name", monitor.name),
                ("Changes", "; ".join(changes)),
                ("Status", "Muted" if monitor.is_mute else "Active"),
            ]
        )

        content = section("Alert Monitor Updated", info)

        return ToolResult(
            content=content,
            data={
                "monitor_id": str(monitor.id),
                "name": monitor.name,
                "changes": changes,
            },
        )
