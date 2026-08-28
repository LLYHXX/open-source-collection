from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import section
from ai_tools.registry import register_tool


class DeletePromptTemplateInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template to delete")


@register_tool
class DeletePromptTemplateTool(BaseTool):
    name = "delete_prompt_template"
    description = (
        "Soft-deletes a prompt template and all its versions. "
        "The template will no longer appear in listings but data is preserved."
    )
    category = "prompts"
    input_model = DeletePromptTemplateInput

    def execute(
        self, params: DeletePromptTemplateInput, context: ToolContext
    ) -> ToolResult:
        from django.db import transaction
        from django.utils import timezone

        from model_hub.models.run_prompt import PromptTemplate, PromptVersion

        try:
            template = PromptTemplate.objects.get(
                id=params.template_id,
                organization=context.organization,
                deleted=False,
            )
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        name = template.name
        now = timezone.now()

        with transaction.atomic():
            # Soft delete the template
            template.deleted = True
            template.deleted_at = now
            template.save(update_fields=["deleted", "deleted_at"])

            # Soft delete all versions
            version_count = PromptVersion.objects.filter(
                original_template=template, deleted=False
            ).update(deleted=True, deleted_at=now)

            # Soft delete related eval configs
            try:
                from model_hub.models.run_prompt import PromptEvalConfig

                PromptEvalConfig.objects.filter(
                    prompt_template=template, deleted=False
                ).update(deleted=True, deleted_at=now)
            except Exception:
                pass

        return ToolResult(
            content=section(
                "Prompt Template Deleted",
                f"Template **{name}** and {version_count} version(s) have been deleted.",
            ),
            data={
                "id": str(params.template_id),
                "name": name,
                "versions_deleted": version_count,
            },
        )
