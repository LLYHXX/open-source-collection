from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    format_datetime,
    format_status,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListEvaluationsInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: pending, processing, completed, failed",
    )
    eval_template_id: Optional[UUID] = Field(
        default=None, description="Filter by evaluation template ID"
    )


@register_tool
class ListEvaluationsTool(BaseTool):
    name = "list_evaluations"
    description = (
        "Lists evaluation results in the current workspace with optional filters. "
        "Returns evaluation name, status, score, model, and creation time."
    )
    category = "evaluations"
    input_model = ListEvaluationsInput

    def execute(self, params: ListEvaluationsInput, context: ToolContext) -> ToolResult:

        from model_hub.models.evaluation import Evaluation, StatusChoices

        # Set workspace context for BaseModelManager auto-filtering

        qs = Evaluation.objects.select_related("eval_template").order_by("-created_at")

        if params.status:
            valid_statuses = {c.value for c in StatusChoices}
            if params.status not in valid_statuses:
                return ToolResult.error(
                    f"Invalid status '{params.status}'. Valid values: {', '.join(sorted(valid_statuses))}",
                    error_code="VALIDATION_ERROR",
                )
            qs = qs.filter(status=params.status)
        if params.eval_template_id:
            qs = qs.filter(eval_template_id=params.eval_template_id)

        total = qs.count()
        evaluations = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for ev in evaluations:
            template_name = ev.eval_template.name if ev.eval_template else "—"
            rows.append(
                [
                    dashboard_link(
                        "evaluation", str(ev.id), label=f"{template_name} (`{ev.id}`)"
                    ),
                    format_status(ev.status),
                    truncate(ev.value, 50) if ev.value else "—",
                    ev.model_name or ev.model or "—",
                    format_datetime(ev.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(ev.id),
                    "template_name": template_name,
                    "status": ev.status,
                    "value": str(ev.value) if ev.value else None,
                    "model": ev.model_name or ev.model,
                }
            )

        table = markdown_table(
            ["Template (ID)", "Status", "Value", "Model", "Created"], rows
        )

        showing = f"Showing {len(rows)} of {total}"
        if params.status:
            showing += f" (filtered by status: {params.status})"

        content = section(f"Evaluations ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(
            content=content, data={"evaluations": data_list, "total": total}
        )
