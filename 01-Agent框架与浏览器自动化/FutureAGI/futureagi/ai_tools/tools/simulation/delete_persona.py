from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DeletePersonaInput(PydanticBaseModel):
    persona_id: UUID = Field(description="The UUID of the persona to delete")


@register_tool
class DeletePersonaTool(BaseTool):
    name = "delete_persona"
    description = "Deletes a workspace persona. System personas cannot be deleted."
    category = "simulation"
    input_model = DeletePersonaInput

    def execute(self, params: DeletePersonaInput, context: ToolContext) -> ToolResult:
        from django.utils import timezone

        from simulate.models.persona import Persona

        try:
            persona = Persona.objects.get(
                id=params.persona_id, organization=context.organization
            )
        except Persona.DoesNotExist:
            return ToolResult.not_found("Persona", str(params.persona_id))

        if persona.persona_type == "system":
            return ToolResult.error(
                "System personas cannot be deleted. Only workspace personas can be removed.",
                error_code="PERMISSION_DENIED",
            )

        persona_name = persona.name
        persona.deleted = True
        persona.deleted_at = timezone.now()
        persona.save(update_fields=["deleted", "deleted_at", "updated_at"])

        info = key_value_block(
            [
                ("ID", f"`{params.persona_id}`"),
                ("Name", persona_name),
                ("Status", "Deleted"),
            ]
        )

        content = section("Persona Deleted", info)

        return ToolResult(
            content=content,
            data={"id": str(params.persona_id), "name": persona_name, "deleted": True},
        )
