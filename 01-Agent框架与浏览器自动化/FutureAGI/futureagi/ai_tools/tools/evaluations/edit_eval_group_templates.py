from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import key_value_block, section
from ai_tools.registry import register_tool


class EditEvalGroupTemplatesInput(PydanticBaseModel):
    eval_group_id: UUID = Field(description="The UUID of the eval group to modify")
    added_template_ids: Optional[list[UUID]] = Field(
        default=None,
        description="List of eval template IDs to add to the group",
    )
    deleted_template_ids: Optional[list[UUID]] = Field(
        default=None,
        description="List of eval template IDs to remove from the group",
    )


@register_tool
class EditEvalGroupTemplatesTool(BaseTool):
    name = "edit_eval_group_templates"
    description = (
        "Adds or removes evaluation templates from an eval group. "
        "At least one of added_template_ids or deleted_template_ids must be provided."
    )
    category = "evaluations"
    input_model = EditEvalGroupTemplatesInput

    def execute(
        self, params: EditEvalGroupTemplatesInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.eval_groups import EvalGroup
        from model_hub.services.eval_group import edit_eval_list_manager

        if not params.added_template_ids and not params.deleted_template_ids:
            return ToolResult.error(
                "At least one of 'added_template_ids' or 'deleted_template_ids' must be provided.",
                error_code="VALIDATION_ERROR",
            )

        try:
            group = EvalGroup.objects.get(
                id=params.eval_group_id,
                organization=context.organization,
            )
        except EvalGroup.DoesNotExist:
            return ToolResult.not_found("Eval Group", str(params.eval_group_id))

        added = (
            [str(tid) for tid in params.added_template_ids]
            if params.added_template_ids
            else []
        )
        deleted = (
            [str(tid) for tid in params.deleted_template_ids]
            if params.deleted_template_ids
            else []
        )

        # Pre-validate that added templates exist and belong to user's org or are system templates
        if added:
            from django.db.models import Q

            from model_hub.models.evals_metric import EvalTemplate

            valid_templates = EvalTemplate.no_workspace_objects.filter(
                Q(organization=context.organization) | Q(organization__isnull=True),
                id__in=added,
            )
            found_ids = {str(t.id) for t in valid_templates}
            missing = [tid for tid in added if tid not in found_ids]
            if missing:
                return ToolResult.error(
                    f"Template(s) not found: {', '.join(missing)}",
                    error_code="NOT_FOUND",
                )

        edit_eval_list_manager(
            eval_group_id=str(params.eval_group_id),
            added_template_ids=added or None,
            deleted_template_ids=deleted or None,
            user=context.user,
        )

        info = key_value_block(
            [
                ("Group", f"`{group.id}` ({group.name})"),
                ("Added", str(len(added)) if added else "0"),
                ("Removed", str(len(deleted)) if deleted else "0"),
            ]
        )

        return ToolResult(
            content=section("Eval Group Templates Updated", info),
            data={
                "group_id": str(params.eval_group_id),
                "added_count": len(added),
                "deleted_count": len(deleted),
            },
        )
