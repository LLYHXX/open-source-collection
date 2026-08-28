from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    format_datetime,
    format_number,
    format_status,
    key_value_block,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetEvaluationInput(PydanticBaseModel):
    evaluation_id: UUID = Field(description="The UUID of the evaluation to retrieve")


@register_tool
class GetEvaluationTool(BaseTool):
    name = "get_evaluation"
    description = (
        "Returns detailed information about a specific evaluation, including "
        "its template, status, scores, model used, runtime, and result explanation."
    )
    category = "evaluations"
    input_model = GetEvaluationInput

    def execute(self, params: GetEvaluationInput, context: ToolContext) -> ToolResult:

        from model_hub.models.evaluation import Evaluation

        try:
            ev = Evaluation.objects.select_related("eval_template").get(
                id=params.evaluation_id, organization=context.organization
            )
        except Evaluation.DoesNotExist:
            return ToolResult.not_found("Evaluation", str(params.evaluation_id))

        template_name = ev.eval_template.name if ev.eval_template else "—"

        info = key_value_block(
            [
                ("ID", f"`{ev.id}`"),
                ("Template", template_name),
                ("Status", format_status(ev.status)),
                ("Model", ev.model_name or ev.model or "—"),
                ("Output Type", ev.output_type or "—"),
                ("Value", str(ev.value) if ev.value is not None else "—"),
                ("Runtime", f"{format_number(ev.runtime)}s" if ev.runtime else "—"),
                ("Created", format_datetime(ev.created_at)),
                (
                    "Link",
                    dashboard_link("evaluation", str(ev.id), label="View in Dashboard"),
                ),
            ]
        )

        content = section(f"Evaluation: {template_name}", info)

        # Add reason if available
        if ev.reason:
            content += f"\n\n### Explanation\n\n{truncate(ev.reason, 1000)}"

        # Add error message if failed
        if ev.status == "failed" and ev.error_message:
            content += f"\n\n### Error\n\n```\n{truncate(ev.error_message, 500)}\n```"

        # Add metrics if available
        if ev.metrics:
            content += "\n\n### Metrics\n\n"
            if isinstance(ev.metrics, dict):
                for key, val in ev.metrics.items():
                    content += f"- **{key}:** {val}\n"
            else:
                content += f"```json\n{truncate(str(ev.metrics), 500)}\n```"

        # Add typed outputs
        typed_outputs = []
        if ev.output_bool is not None:
            typed_outputs.append(
                ("Boolean Result", "Pass" if ev.output_bool else "Fail")
            )
        if ev.output_float is not None:
            typed_outputs.append(("Numeric Result", format_number(ev.output_float)))
        if ev.output_str:
            typed_outputs.append(("Text Result", truncate(ev.output_str, 200)))

        if typed_outputs:
            content += "\n\n### Results\n\n"
            content += key_value_block(typed_outputs)

        data = {
            "id": str(ev.id),
            "template_name": template_name,
            "status": ev.status,
            "value": str(ev.value) if ev.value is not None else None,
            "model": ev.model_name or ev.model,
            "runtime": ev.runtime,
            "output_type": ev.output_type,
            "reason": ev.reason,
            "metrics": ev.metrics,
        }

        return ToolResult(content=content, data=data)
