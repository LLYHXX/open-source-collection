from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    markdown_table,
    section,
)
from ai_tools.registry import register_tool


class ListAnnotationQueuesInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: draft, active, paused, completed",
    )
    search: Optional[str] = Field(default=None, description="Search queues by name")


@register_tool
class ListAnnotationQueuesTool(BaseTool):
    name = "list_annotation_queues"
    description = "Lists annotation queues in the workspace with optional status and search filters."
    category = "annotations"
    input_model = ListAnnotationQueuesInput

    def execute(
        self, params: ListAnnotationQueuesInput, context: ToolContext
    ) -> ToolResult:
        from django.db.models import Count, Q

        from model_hub.models.annotation_queues import AnnotationQueue

        qs = AnnotationQueue.objects.filter(
            organization=context.organization, deleted=False
        ).order_by("-created_at")

        if params.status:
            qs = qs.filter(status=params.status)
        if params.search:
            qs = qs.filter(name__icontains=params.search)

        total = qs.count()
        queues = qs.annotate(
            item_count=Count("items", filter=Q(items__deleted=False)),
            completed_count=Count(
                "items", filter=Q(items__deleted=False, items__status="completed")
            ),
        )[params.offset : params.offset + params.limit]

        if not queues:
            return ToolResult(
                content=section("Annotation Queues", "No queues found."),
                data={"queues": [], "total": 0},
            )

        rows = []
        data_list = []
        for q in queues:
            scope = "—"
            if q.project_id:
                scope = "Project"
            elif q.dataset_id:
                scope = "Dataset"
            elif q.agent_definition_id:
                scope = "Agent"

            rows.append(
                [
                    f"`{q.id}`",
                    q.name,
                    q.status,
                    scope,
                    str(q.item_count),
                    str(q.completed_count),
                    format_datetime(q.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(q.id),
                    "name": q.name,
                    "status": q.status,
                    "item_count": q.item_count,
                    "completed_count": q.completed_count,
                }
            )

        table = markdown_table(
            ["ID", "Name", "Status", "Scope", "Items", "Done", "Created"], rows
        )
        content = section(f"Annotation Queues ({total})", table)

        return ToolResult(content=content, data={"queues": data_list, "total": total})
