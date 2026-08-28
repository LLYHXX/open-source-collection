from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListAlertMonitorsInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    project_id: Optional[UUID] = Field(default=None, description="Filter by project ID")


@register_tool
class ListAlertMonitorsTool(BaseTool):
    name = "list_alert_monitors"
    description = (
        "Lists alert monitors in the workspace. Monitors track metrics like "
        "error rates, response times, token usage, and evaluation scores, "
        "and trigger alerts when thresholds are exceeded."
    )
    category = "tracing"
    input_model = ListAlertMonitorsInput

    def execute(
        self, params: ListAlertMonitorsInput, context: ToolContext
    ) -> ToolResult:

        from tracer.models.monitor import UserAlertMonitor

        qs = (
            UserAlertMonitor.objects.filter(organization=context.organization)
            .select_related("project")
            .order_by("-created_at")
        )

        if params.project_id:
            qs = qs.filter(project_id=params.project_id)

        total = qs.count()
        monitors = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for m in monitors:
            project_name = m.project.name if m.project else "All"
            muted = "Muted" if m.is_mute else "Active"
            threshold = "—"
            if m.critical_threshold_value is not None:
                threshold = f"Critical: {m.critical_threshold_value}"
            elif m.warning_threshold_value is not None:
                threshold = f"Warning: {m.warning_threshold_value}"

            rows.append(
                [
                    f"`{m.id}`",
                    truncate(m.name, 30),
                    m.metric_type or "—",
                    project_name,
                    muted,
                    threshold,
                    format_datetime(m.last_checked_at),
                ]
            )
            data_list.append(
                {
                    "id": str(m.id),
                    "name": m.name,
                    "metric_type": m.metric_type,
                    "project": project_name,
                    "is_mute": m.is_mute,
                    "alert_frequency": m.alert_frequency,
                }
            )

        table = markdown_table(
            ["ID", "Name", "Metric", "Project", "Status", "Threshold", "Last Check"],
            rows,
        )

        showing = f"Showing {len(rows)} of {total}"
        content = section(f"Alert Monitors ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(content=content, data={"monitors": data_list, "total": total})
