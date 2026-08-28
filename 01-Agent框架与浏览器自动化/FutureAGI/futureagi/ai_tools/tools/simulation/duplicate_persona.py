from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DuplicatePersonaInput(PydanticBaseModel):
    persona_id: UUID = Field(description="The UUID of the persona to duplicate")
    new_name: str = Field(description="Name for the duplicated persona")


@register_tool
class DuplicatePersonaTool(BaseTool):
    name = "duplicate_persona"
    description = (
        "Creates a copy of an existing persona with a new name. "
        "All configuration is cloned. The clone is always a workspace persona."
    )
    category = "simulation"
    input_model = DuplicatePersonaInput

    def execute(
        self, params: DuplicatePersonaInput, context: ToolContext
    ) -> ToolResult:

        from simulate.models.persona import Persona

        try:
            original = Persona.objects.get(
                id=params.persona_id, organization=context.organization
            )
        except Persona.DoesNotExist:
            return ToolResult.not_found("Persona", str(params.persona_id))

        # Check for duplicate name (matches PersonaViewSet._duplicate_persona)
        if Persona.objects.filter(
            name__iexact=params.new_name,
            workspace=context.workspace,
            persona_type="workspace",
            deleted=False,
        ).exists():
            return ToolResult.error(
                f"A persona named '{params.new_name}' already exists in this workspace.",
                error_code="VALIDATION_ERROR",
            )

        clone = Persona(
            name=params.new_name,
            description=original.description,
            persona_type="workspace",
            simulation_type=original.simulation_type,
            gender=original.gender,
            age_group=original.age_group,
            occupation=original.occupation,
            location=original.location,
            personality=original.personality,
            communication_style=original.communication_style,
            multilingual=original.multilingual,
            languages=original.languages,
            accent=original.accent,
            conversation_speed=original.conversation_speed,
            background_sound=original.background_sound,
            finished_speaking_sensitivity=original.finished_speaking_sensitivity,
            interrupt_sensitivity=original.interrupt_sensitivity,
            keywords=original.keywords,
            metadata=original.metadata,
            additional_instruction=original.additional_instruction,
            tone=original.tone,
            verbosity=original.verbosity,
            punctuation=original.punctuation,
            slang_usage=original.slang_usage,
            typos_frequency=original.typos_frequency,
            regional_mix=original.regional_mix,
            emoji_usage=original.emoji_usage,
            organization=context.organization,
            workspace=context.workspace,
        )
        clone.save()

        info = key_value_block(
            [
                ("New ID", f"`{clone.id}`"),
                ("New Name", clone.name),
                ("Cloned From", f"`{original.id}` ({original.name})"),
                ("Type", "workspace"),
                ("Simulation Type", clone.simulation_type),
                ("Created", format_datetime(clone.created_at)),
            ]
        )

        content = section("Persona Duplicated", info)

        return ToolResult(
            content=content,
            data={
                "id": str(clone.id),
                "name": clone.name,
                "cloned_from": str(original.id),
            },
        )
