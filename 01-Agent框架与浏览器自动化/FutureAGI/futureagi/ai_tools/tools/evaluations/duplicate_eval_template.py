from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import key_value_block, section
from ai_tools.registry import register_tool


class DuplicateEvalTemplateInput(PydanticBaseModel):
    eval_template_id: str = Field(
        description="Name or UUID of the eval template to duplicate"
    )
    name: str = Field(
        description="Name for the new duplicated template",
        min_length=1,
        max_length=2000,
    )


@register_tool
class DuplicateEvalTemplateTool(BaseTool):
    name = "duplicate_eval_template"
    description = (
        "Duplicates a user-owned evaluation template with a new name. "
        "All fields are copied except ID, timestamps, and name. "
        "Only USER-owned templates can be duplicated."
    )
    category = "evaluations"
    input_model = DuplicateEvalTemplateInput

    def execute(
        self, params: DuplicateEvalTemplateInput, context: ToolContext
    ) -> ToolResult:
        from django.utils import timezone

        from ai_tools.resolvers import resolve_eval_template
        from model_hub.models.choices import OwnerChoices
        from model_hub.models.evals_metric import EvalTemplate

        template_obj, err = resolve_eval_template(
            params.eval_template_id, context.organization
        )
        if err:
            return ToolResult.error(err, error_code="NOT_FOUND")

        try:
            template = EvalTemplate.objects.get(
                id=template_obj.id,
                organization=context.organization,
                owner=OwnerChoices.USER.value,
                deleted=False,
            )
        except EvalTemplate.DoesNotExist:
            return ToolResult.not_found(
                "User-owned Eval Template", str(template_obj.id)
            )

        # Validate name pattern
        import re

        clean_name = params.name.strip()
        if not re.match(r"^[0-9a-z_-]+$", clean_name):
            return ToolResult.error(
                "Name can only contain lowercase alphabets, numbers, hyphens (-), or underscores (_).",
                error_code="VALIDATION_ERROR",
            )
        if clean_name[0] in "-_" or clean_name[-1] in "-_":
            return ToolResult.error(
                "Name cannot start or end with hyphens (-) or underscores (_).",
                error_code="VALIDATION_ERROR",
            )
        if "_-" in clean_name or "-_" in clean_name:
            return ToolResult.error(
                "Name cannot contain consecutive mixed separators (_- or -_).",
                error_code="VALIDATION_ERROR",
            )

        # Check name uniqueness
        if EvalTemplate.objects.filter(
            name=params.name,
            organization=context.organization,
            owner=OwnerChoices.USER.value,
            deleted=False,
        ).exists():
            return ToolResult.error(
                f"An eval template named '{params.name}' already exists.",
                error_code="VALIDATION_ERROR",
            )

        # Copy all fields except id, timestamps, and name
        now = timezone.now()
        fields_to_copy = {
            field.name: getattr(template, field.name)
            for field in template._meta.fields
            if field.name not in ["id", "created_at", "updated_at", "name"]
        }
        fields_to_copy["name"] = params.name
        fields_to_copy["organization"] = context.organization
        fields_to_copy["created_at"] = now
        fields_to_copy["updated_at"] = now

        new_template = EvalTemplate.objects.create(**fields_to_copy)

        info = key_value_block(
            [
                ("New ID", f"`{new_template.id}`"),
                ("Name", new_template.name),
                ("Cloned From", f"`{template.id}` ({template.name})"),
            ]
        )

        return ToolResult(
            content=section("Eval Template Duplicated", info),
            data={
                "id": str(new_template.id),
                "name": new_template.name,
                "source_id": str(template.id),
                "source_name": template.name,
            },
        )
