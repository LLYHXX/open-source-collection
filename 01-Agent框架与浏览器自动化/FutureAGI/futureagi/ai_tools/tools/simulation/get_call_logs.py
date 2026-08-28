from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    key_value_block,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetCallLogsInput(PydanticBaseModel):
    call_execution_id: UUID = Field(description="The UUID of the call execution")
    limit: int = Field(
        default=50, ge=1, le=200, description="Max log entries to return"
    )
    source: Optional[str] = Field(
        default=None, description="Filter by source: agent or customer"
    )


@register_tool
class GetCallLogsTool(BaseTool):
    name = "get_call_logs"
    description = (
        "Returns log entries for a call execution. "
        "Shows timestamp, severity, category, and message body."
    )
    category = "simulation"
    input_model = GetCallLogsInput

    def execute(self, params: GetCallLogsInput, context: ToolContext) -> ToolResult:

        from simulate.models.call_log_entry import CallLogEntry
        from simulate.models.test_execution import CallExecution

        try:
            call = CallExecution.objects.get(id=params.call_execution_id)
        except CallExecution.DoesNotExist:
            return ToolResult.not_found("Call Execution", str(params.call_execution_id))

        qs = CallLogEntry.objects.filter(call_execution=call).order_by("logged_at")

        if params.source:
            qs = qs.filter(source=params.source)

        total = qs.count()
        logs = qs[: params.limit]

        info = key_value_block(
            [
                ("Call ID", f"`{call.id}`"),
                ("Total Log Entries", str(total)),
                ("Showing", str(min(total, params.limit))),
            ]
        )

        content = section(f"Call Logs", info)

        if not logs:
            content += "\n\n_No log entries found for this call._"
            return ToolResult(
                content=content,
                data={"call_id": str(call.id), "logs": [], "total": 0},
            )

        rows = []
        log_data = []
        for log in logs:
            rows.append(
                [
                    format_datetime(log.logged_at),
                    log.severity_text or str(log.level),
                    log.source,
                    log.category or "—",
                    truncate(log.body, 80),
                ]
            )
            log_data.append(
                {
                    "id": str(log.id),
                    "logged_at": log.logged_at.isoformat() if log.logged_at else None,
                    "level": log.level,
                    "severity": log.severity_text,
                    "source": log.source,
                    "category": log.category,
                    "body": log.body,
                }
            )

        table = markdown_table(
            ["Time", "Severity", "Source", "Category", "Message"], rows
        )
        content += f"\n\n{table}"

        if total > params.limit:
            content += f"\n\n_Showing {params.limit} of {total} entries. Use limit parameter to see more._"

        return ToolResult(
            content=content,
            data={"call_id": str(call.id), "logs": log_data, "total": total},
        )
