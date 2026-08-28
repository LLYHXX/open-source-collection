from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    key_value_block,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetPersonaInput(PydanticBaseModel):
    persona_id: UUID = Field(description="The UUID of the persona to retrieve")


@register_tool
class GetPersonaTool(BaseTool):
    name = "get_persona"
    description = (
        "Returns detailed information about a specific persona, "
        "including demographics, behavioral traits, speech characteristics, "
        "and text settings."
    )
    category = "simulation"
    input_model = GetPersonaInput

    def execute(self, params: GetPersonaInput, context: ToolContext) -> ToolResult:

        from simulate.models.persona import Persona

        try:
            persona = Persona.objects.get(
                id=params.persona_id, organization=context.organization
            )
        except Persona.DoesNotExist:
            return ToolResult.not_found("Persona", str(params.persona_id))

        def list_str(val):
            if val and isinstance(val, list):
                return ", ".join(str(v) for v in val)
            return "—"

        info = key_value_block(
            [
                ("ID", f"`{persona.id}`"),
                ("Name", persona.name),
                ("Persona Type", persona.persona_type),
                ("Simulation Type", persona.simulation_type),
                (
                    "Description",
                    truncate(persona.description, 300) if persona.description else "—",
                ),
                ("Created", format_datetime(persona.created_at)),
            ]
        )

        content = section(f"Persona: {persona.name}", info)

        # Demographics
        demographics = key_value_block(
            [
                ("Gender", list_str(persona.gender)),
                ("Age Group", list_str(persona.age_group)),
                ("Occupation", list_str(persona.occupation)),
                ("Location", list_str(persona.location)),
            ]
        )
        content += f"\n\n### Demographics\n\n{demographics}"

        # Behavioral Profile
        behavioral = key_value_block(
            [
                ("Personality", list_str(persona.personality)),
                ("Communication Style", list_str(persona.communication_style)),
                ("Tone", persona.tone or "—"),
                ("Verbosity", persona.verbosity or "—"),
            ]
        )
        content += f"\n\n### Behavioral Profile\n\n{behavioral}"

        # Speech Characteristics (voice-specific)
        if persona.simulation_type == "voice":
            speech = key_value_block(
                [
                    ("Languages", list_str(persona.languages)),
                    ("Accent", list_str(persona.accent)),
                    ("Conversation Speed", list_str(persona.conversation_speed)),
                    ("Multilingual", "Yes" if persona.multilingual else "No"),
                    ("Background Sound", "Yes" if persona.background_sound else "No"),
                    ("Interrupt Sensitivity", list_str(persona.interrupt_sensitivity)),
                    (
                        "Finished Speaking Sensitivity",
                        list_str(persona.finished_speaking_sensitivity),
                    ),
                ]
            )
            content += f"\n\n### Speech Characteristics\n\n{speech}"

        # Text Settings (text-specific)
        if persona.simulation_type == "text":
            text_settings = key_value_block(
                [
                    ("Punctuation", persona.punctuation or "—"),
                    ("Slang Usage", persona.slang_usage or "—"),
                    ("Typos Frequency", persona.typos_frequency or "—"),
                    ("Regional Mix", persona.regional_mix or "—"),
                    ("Emoji Usage", persona.emoji_usage or "—"),
                ]
            )
            content += f"\n\n### Text Settings\n\n{text_settings}"

        # Additional instructions
        if persona.additional_instruction:
            content += f"\n\n### Additional Instructions\n\n{truncate(persona.additional_instruction, 500)}"

        # Keywords
        if persona.keywords:
            content += f"\n\n### Keywords\n\n{list_str(persona.keywords)}"

        data = {
            "id": str(persona.id),
            "name": persona.name,
            "persona_type": persona.persona_type,
            "simulation_type": persona.simulation_type,
            "gender": persona.gender,
            "personality": persona.personality,
            "tone": persona.tone,
            "verbosity": persona.verbosity,
        }

        return ToolResult(content=content, data=data)
