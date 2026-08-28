from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import key_value_block, section
from ai_tools.registry import register_tool


class CommitPromptVersionInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template")
    version_name: str = Field(
        description="The version name to commit (e.g., 'v1', 'v2')"
    )
    message: Optional[str] = Field(default=None, description="Commit message")
    set_default: bool = Field(default=False, description="Set this version as default")


@register_tool
class CommitPromptVersionTool(BaseTool):
    name = "commit_prompt_version"
    description = (
        "Commits a draft prompt version, optionally setting it as default. "
        "Adds a commit message to the version and marks it as committed (non-draft)."
    )
    category = "prompts"
    input_model = CommitPromptVersionInput

    def execute(
        self, params: CommitPromptVersionInput, context: ToolContext
    ) -> ToolResult:
        from django.utils import timezone

        from model_hub.models.run_prompt import PromptTemplate, PromptVersion

        try:
            template = PromptTemplate.objects.get(id=params.template_id)
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        try:
            version = PromptVersion.objects.get(
                original_template=template,
                template_version=params.version_name,
            )
        except PromptVersion.DoesNotExist:
            return ToolResult.not_found("Prompt Version", params.version_name)

        version.commit_message = params.message or ""
        version.is_draft = False
        if params.set_default:
            version.is_default = True
        version.updated_at = timezone.now()
        version.save(
            update_fields=["is_default", "commit_message", "updated_at", "is_draft"]
        )

        info = key_value_block(
            [
                ("Template", template.name),
                ("Version", version.template_version),
                ("Commit Message", version.commit_message or "—"),
                ("Is Default", "Yes" if version.is_default else "No"),
            ]
        )

        content = section("Version Committed", info)

        return ToolResult(
            content=content,
            data={
                "template_id": str(template.id),
                "version_id": str(version.id),
                "version": version.template_version,
                "is_default": version.is_default,
            },
        )
