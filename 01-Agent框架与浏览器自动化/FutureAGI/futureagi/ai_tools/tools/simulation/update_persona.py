from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool
from ai_tools.tools.simulation.create_persona import (
    Accent,
    AgeGroup,
    CommunicationStyle,
    ConversationSpeed,
    EmojiUsage,
    Gender,
    Language,
    Location,
    Occupation,
    Personality,
    Punctuation,
    RegionalMix,
    SlangUsage,
    Tone,
    TypoFrequency,
    Verbosity,
)


class UpdatePersonaInput(PydanticBaseModel):
    persona_id: UUID = Field(description="The UUID of the persona to update")
    name: Optional[str] = Field(default=None, description="New name")
    description: Optional[str] = Field(default=None, description="New description")
    # Demographics
    gender: Optional[List[Gender]] = Field(default=None, description="New gender list")
    age_group: Optional[List[AgeGroup]] = Field(
        default=None, description="New age group list"
    )
    occupation: Optional[List[Occupation]] = Field(
        default=None, description="New occupation list"
    )
    location: Optional[List[Location]] = Field(
        default=None, description="New location list"
    )
    # Behavioral
    personality: Optional[List[Personality]] = Field(
        default=None, description="New personality list"
    )
    communication_style: Optional[List[CommunicationStyle]] = Field(
        default=None, description="New communication style list"
    )
    accent: Optional[List[Accent]] = Field(
        default=None, description="New accent list. Voice only."
    )
    # Voice settings
    multilingual: Optional[bool] = Field(
        default=None, description="Whether the persona supports multiple languages"
    )
    languages: Optional[List[Language]] = Field(
        default=None, description="New languages list"
    )
    conversation_speed: Optional[List[ConversationSpeed]] = Field(
        default=None, description="New conversation speed values. Voice only."
    )
    background_sound: Optional[bool] = Field(
        default=None, description="Enable background sound. Voice only."
    )
    finished_speaking_sensitivity: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Finished speaking sensitivity (1-10). Voice only.",
    )
    interrupt_sensitivity: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Interrupt sensitivity (1-10). Voice only.",
    )
    keywords: Optional[List[str]] = Field(default=None, description="New keywords list")
    # Chat settings
    tone: Optional[Tone] = Field(default=None, description="New tone. Chat only.")
    verbosity: Optional[Verbosity] = Field(
        default=None, description="New verbosity level. Chat only."
    )
    punctuation: Optional[Punctuation] = Field(
        default=None, description="New punctuation style. Chat only."
    )
    emoji_usage: Optional[EmojiUsage] = Field(
        default=None, description="New emoji usage level. Chat only."
    )
    slang_usage: Optional[SlangUsage] = Field(
        default=None, description="New slang usage level. Chat only."
    )
    typos_frequency: Optional[TypoFrequency] = Field(
        default=None, description="New typo frequency. Chat only."
    )
    regional_mix: Optional[RegionalMix] = Field(
        default=None, description="New regional language mix level. Chat only."
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None, description="New custom key-value properties"
    )
    additional_instruction: Optional[str] = Field(
        default=None, description="New additional instructions"
    )

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v):
        if v and isinstance(v, dict):
            for key, value in v.items():
                if not key or not str(key).strip():
                    raise ValueError("Custom property keys must be non-empty strings.")
                if not value or not str(value).strip():
                    raise ValueError(
                        f"Value for property '{key}' must be a non-empty string."
                    )
        return v


@register_tool
class UpdatePersonaTool(BaseTool):
    name = "update_persona"
    description = "Updates an existing persona. Only provided fields will be changed."
    category = "simulation"
    input_model = UpdatePersonaInput

    def execute(self, params: UpdatePersonaInput, context: ToolContext) -> ToolResult:

        from simulate.models.persona import Persona

        try:
            persona = Persona.objects.get(
                id=params.persona_id, organization=context.organization
            )
        except Persona.DoesNotExist:
            return ToolResult.not_found("Persona", str(params.persona_id))

        if persona.persona_type == "system":
            return ToolResult.error(
                "System personas cannot be modified.",
                error_code="PERMISSION_DENIED",
            )

        updated_fields = []
        field_map = {
            "name": params.name,
            "description": params.description,
            "gender": params.gender,
            "age_group": params.age_group,
            "occupation": params.occupation,
            "location": params.location,
            "personality": params.personality,
            "communication_style": params.communication_style,
            "accent": params.accent,
            "multilingual": params.multilingual,
            "languages": params.languages,
            "conversation_speed": params.conversation_speed,
            "background_sound": params.background_sound,
            "finished_speaking_sensitivity": params.finished_speaking_sensitivity,
            "interrupt_sensitivity": params.interrupt_sensitivity,
            "keywords": params.keywords,
            "tone": params.tone,
            "verbosity": params.verbosity,
            "punctuation": params.punctuation,
            "emoji_usage": params.emoji_usage,
            "slang_usage": params.slang_usage,
            "typos_frequency": params.typos_frequency,
            "regional_mix": params.regional_mix,
            "metadata": params.metadata,
            "additional_instruction": params.additional_instruction,
        }

        for field_name, value in field_map.items():
            if value is not None:
                setattr(persona, field_name, value)
                updated_fields.append(field_name)

        if not updated_fields:
            return ToolResult.error(
                "No fields provided to update.",
                error_code="VALIDATION_ERROR",
            )

        persona.save(update_fields=updated_fields + ["updated_at"])

        info = key_value_block(
            [
                ("ID", f"`{persona.id}`"),
                ("Name", persona.name),
                ("Updated Fields", ", ".join(updated_fields)),
                ("Updated At", format_datetime(persona.updated_at)),
            ]
        )

        content = section("Persona Updated", info)

        return ToolResult(
            content=content,
            data={
                "id": str(persona.id),
                "name": persona.name,
                "updated_fields": updated_fields,
            },
        )
