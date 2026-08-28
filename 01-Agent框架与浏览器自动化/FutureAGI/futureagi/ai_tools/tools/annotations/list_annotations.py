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


class ListAnnotationsInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    dataset_id: Optional[UUID] = Field(default=None, description="Filter by dataset ID")


@register_tool
class ListAnnotationsTool(BaseTool):
    name = "list_annotations"
    description = (
        "Lists annotation tasks in the current workspace. "
        "Annotation tasks allow human reviewers to label dataset rows "
        "using various label types (text, numeric, categorical, star, thumbs up/down). "
        "Returns task name, dataset, assigned users, label count, and progress."
    )
    category = "annotations"
    input_model = ListAnnotationsInput

    def execute(self, params: ListAnnotationsInput, context: ToolContext) -> ToolResult:

        from model_hub.models.develop_annotations import Annotations

        qs = (
            Annotations.objects.select_related("dataset")
            .prefetch_related("labels", "assigned_users")
            .order_by("-created_at")
        )

        if params.dataset_id:
            qs = qs.filter(dataset_id=params.dataset_id)

        total = qs.count()
        annotations = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for ann in annotations:
            dataset_name = ann.dataset.name if ann.dataset else "—"
            user_count = ann.assigned_users.count()
            label_count = ann.labels.count()
            responses = ann.responses or 1

            # Parse summary for progress
            summary = ann.summary or {}
            progress = "—"
            if (
                isinstance(summary, dict)
                and "completed" in summary
                and "total" in summary
            ):
                completed = summary.get("completed", 0)
                total_rows = summary.get("total", 0)
                if total_rows > 0:
                    pct = int(completed / total_rows * 100)
                    progress = f"{completed}/{total_rows} ({pct}%)"

            rows.append(
                [
                    f"`{ann.id}`",
                    truncate(ann.name, 35),
                    truncate(dataset_name, 25),
                    str(user_count),
                    str(label_count),
                    str(responses),
                    progress,
                    format_datetime(ann.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(ann.id),
                    "name": ann.name,
                    "dataset": dataset_name,
                    "dataset_id": str(ann.dataset_id) if ann.dataset_id else None,
                    "assigned_users": user_count,
                    "label_count": label_count,
                    "responses_required": responses,
                }
            )

        table = markdown_table(
            [
                "ID",
                "Name",
                "Dataset",
                "Users",
                "Labels",
                "Responses",
                "Progress",
                "Created",
            ],
            rows,
        )

        showing = f"Showing {len(rows)} of {total}"
        if params.dataset_id:
            showing += f" (dataset: {params.dataset_id})"

        content = section(f"Annotation Tasks ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(
            content=content, data={"annotations": data_list, "total": total}
        )
