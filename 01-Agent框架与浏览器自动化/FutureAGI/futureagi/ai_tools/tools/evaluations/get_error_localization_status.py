from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import format_datetime, key_value_block, section
from ai_tools.registry import register_tool


class GetErrorLocalizationStatusInput(PydanticBaseModel):
    task_id: UUID = Field(
        description="The UUID of the ErrorLocalizerTask to check status for"
    )


@register_tool
class GetErrorLocalizationStatusTool(BaseTool):
    name = "get_error_localization_status"
    description = (
        "Checks the status of an error localization task. "
        "Returns PENDING, RUNNING, COMPLETED, FAILED, or SKIPPED."
    )
    category = "evaluations"
    input_model = GetErrorLocalizationStatusInput

    def execute(
        self, params: GetErrorLocalizationStatusInput, context: ToolContext
    ) -> ToolResult:
        from model_hub.models.error_localizer_model import ErrorLocalizerTask

        try:
            task = ErrorLocalizerTask.objects.get(
                id=params.task_id,
                organization=context.organization,
            )
        except ErrorLocalizerTask.DoesNotExist:
            return ToolResult.not_found("Error Localization Task", str(params.task_id))

        info = key_value_block(
            [
                ("Task ID", f"`{task.id}`"),
                ("Status", task.status.upper()),
                ("Source", task.source),
                ("Template", task.eval_template.name if task.eval_template else "—"),
                ("Selected Input Key", task.selected_input_key or "—"),
                ("Created", format_datetime(task.created_at)),
            ]
        )

        if task.error_message:
            info += f"\n**Error:** {task.error_message}"

        return ToolResult(
            content=section("Error Localization Status", info),
            data={
                "task_id": str(task.id),
                "status": task.status,
                "source": task.source,
                "error_message": task.error_message,
                "selected_input_key": task.selected_input_key,
            },
        )
