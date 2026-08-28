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


class ListSessionsInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    project_id: Optional[UUID] = Field(default=None, description="Filter by project ID")


@register_tool
class ListSessionsTool(BaseTool):
    name = "list_sessions"
    description = (
        "Lists trace sessions in the current workspace. Sessions group related "
        "traces together (e.g., a multi-turn conversation). Shows session name, "
        "project, trace count, and timing."
    )
    category = "tracing"
    input_model = ListSessionsInput

    def execute(self, params: ListSessionsInput, context: ToolContext) -> ToolResult:
        from django.db.models import Count, Max, Min

        from tracer.models.project import Project
        from tracer.models.trace_session import TraceSession

        # Scope sessions to projects accessible in the current workspace
        accessible_project_ids = Project.objects.filter(
            organization=context.organization
        ).values_list("id", flat=True)

        qs = (
            TraceSession.objects.select_related("project")
            .filter(project_id__in=accessible_project_ids)
            .annotate(
                trace_count=Count("traces"),
                first_trace_time=Min("traces__created_at"),
                last_trace_time=Max("traces__created_at"),
            )
            .order_by("-created_at")
        )

        if params.project_id:
            qs = qs.filter(project_id=params.project_id)

        total = qs.count()
        sessions = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for s in sessions:
            project_name = s.project.name if s.project else "—"
            rows.append(
                [
                    f"`{s.id}`",
                    truncate(s.name, 30) if s.name else "—",
                    project_name,
                    str(s.trace_count),
                    "Yes" if s.bookmarked else "No",
                    format_datetime(s.first_trace_time),
                    format_datetime(s.last_trace_time),
                    format_datetime(s.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(s.id),
                    "name": s.name,
                    "project": project_name,
                    "trace_count": s.trace_count,
                    "bookmarked": s.bookmarked,
                }
            )

        table = markdown_table(
            [
                "ID",
                "Name",
                "Project",
                "Traces",
                "Bookmarked",
                "First Trace",
                "Last Trace",
                "Created",
            ],
            rows,
        )

        showing = f"Showing {len(rows)} of {total}"
        if params.project_id:
            showing += f" (project: {params.project_id})"

        content = section(f"Sessions ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(content=content, data={"sessions": data_list, "total": total})
