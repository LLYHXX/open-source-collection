from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import section
from ai_tools.registry import register_tool


class DeleteEvalGroupInput(PydanticBaseModel):
    eval_group_id: UUID = Field(description="The UUID of the eval group to delete")


@register_tool
class DeleteEvalGroupTool(BaseTool):
    name = "delete_eval_group"
    description = (
        "Deletes an evaluation group (soft delete). "
        "This removes the group and clears all template associations."
    )
    category = "evaluations"
    input_model = DeleteEvalGroupInput

    def execute(self, params: DeleteEvalGroupInput, context: ToolContext) -> ToolResult:

        from model_hub.models.eval_groups import EvalGroup

        try:
            group = EvalGroup.objects.get(
                id=params.eval_group_id,
                organization=context.organization,
            )
        except EvalGroup.DoesNotExist:
            return ToolResult.not_found("Eval Group", str(params.eval_group_id))

        from django.utils import timezone

        name = group.name

        # Soft delete + clear M2M
        group.deleted = True
        group.deleted_at = timezone.now()
        group.save(update_fields=["deleted", "deleted_at"])
        group.eval_templates.through.objects.filter(evalgroup_id=group.id).delete()

        return ToolResult(
            content=section(
                "Eval Group Deleted", f"Group **{name}** has been deleted."
            ),
            data={"id": str(params.eval_group_id), "name": name},
        )
