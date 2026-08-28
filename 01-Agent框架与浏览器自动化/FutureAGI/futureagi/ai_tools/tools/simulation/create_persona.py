from typing import Dict, List, Literal, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool

# Literal types mirroring Django model choices on simulate.models.persona.Persona.
# Exposing these as Literal produces JSON Schema ``enum`` arrays so MCP clients
# can present valid options to users without a round-trip.

SimulationType = Literal["voice", "text"]

Gender = Literal["male", "female"]

AgeGroup = Literal["18-25", "25-32", "32-40", "40-50", "50-60", "60+"]

Location = Literal["United States", "Canada", "United Kingdom", "Australia", "India"]

Occupation = Literal[
    "Student",
    "Teacher",
    "Engineer",
    "Doctor",
    "Nurse",
    "Business Owner",
    "Manager",
    "Sales Representative",
    "Customer Service",
    "Technician",
    "Consultant",
    "Accountant",
    "Marketing Professional",
    "Retired",
    "Homemaker",
    "Freelancer",
    "Other",
]

Personality = Literal[
    "Friendly and cooperative",
    "Professional and formal",
    "Cautious and skeptical",
    "Impatient and direct",
    "Detail-oriented",
    "Easy-going",
    "Anxious",
    "Confident",
    "Analytical",
    "Emotional",
    "Reserved",
    "Talkative",
]

CommunicationStyle = Literal[
    "Direct and concise",
    "Detailed and elaborate",
    "Casual and friendly",
    "Formal and polite",
    "Technical",
    "Simple and clear",
    "Questioning",
    "Assertive",
    "Passive",
    "Collaborative",
]

Accent = Literal["American", "Australian", "Indian", "Canadian", "Neutral"]

Language = Literal["English", "Hindi"]

ConversationSpeed = Literal["0.5", "0.75", "1.0", "1.25", "1.5"]

Tone = Literal["formal", "casual", "neutral"]

Verbosity = Literal["brief", "balanced", "detailed"]

Punctuation = Literal["clean", "minimal", "expressive", "erratic"]

EmojiUsage = Literal["never", "light", "regular", "heavy"]

SlangUsage = Literal["none", "light", "moderate", "heavy"]

TypoFrequency = Literal["none", "rare", "occasional", "frequent"]

RegionalMix = Literal["none", "light", "moderate", "heavy"]


def _get_persona_choices():
    """Lazy import to avoid circular imports at module load time."""
    from simulate.models.persona import Persona

    return {
        "simulation_type": [c[0] for c in Persona.SimulationTypeChoices.choices],
        "gender": [c[0] for c in Persona.GenderChoices.choices],
        "age_group": [c[0] for c in Persona.AgeGroupChoices.choices],
        "location": [c[0] for c in Persona.LocationChoices.choices],
        "occupation": [c[0] for c in Persona.ProfessionChoices.choices],
        "personality": [c[0] for c in Persona.PersonalityChoices.choices],
        "communication_style": [
            c[0] for c in Persona.CommunicationStyleChoices.choices
        ],
        "accent": [c[0] for c in Persona.AccentChoices.choices],
        "language": [c[0] for c in Persona.LanguageChoices.choices],
        "conversation_speed": [c[0] for c in Persona.ConversationSpeedChoices.choices],
        "tone": [c[0] for c in Persona.PersonaToneChoices.choices],
        "verbosity": [c[0] for c in Persona.PersonaVerbosityChoices.choices],
        "punctuation": [c[0] for c in Persona.PunctuationChoices.choices],
        "emoji_usage": [c[0] for c in Persona.EmojiUsageChoices.choices],
        "slang_usage": [c[0] for c in Persona.StandardUsageChoices.choices],
        "typos_frequency": [c[0] for c in Persona.TypoLevelChoices.choices],
        "regional_mix": [c[0] for c in Persona.StandardUsageChoices.choices],
    }


class CreatePersonaInput(PydanticBaseModel):
    name: str = Field(description="Name of the persona")
    description: str = Field(description="Description of the persona")
    simulation_type: SimulationType = Field(
        default="voice", description="Simulation type"
    )
    # Demographics
    gender: Optional[List[Gender]] = Field(default=None, description="List of genders")
    age_group: Optional[List[AgeGroup]] = Field(
        default=None, description="List of age groups"
    )
    occupation: Optional[List[Occupation]] = Field(
        default=None, description="List of occupations"
    )
    location: Optional[List[Location]] = Field(
        default=None, description="List of locations"
    )
    # Behavioral
    personality: Optional[List[Personality]] = Field(
        default=None, description="List of personality types"
    )
    communication_style: Optional[List[CommunicationStyle]] = Field(
        default=None, description="List of communication styles"
    )
    accent: Optional[List[Accent]] = Field(
        default=None, description="List of accents. Voice only."
    )
    # Voice conversation settings
    multilingual: Optional[bool] = Field(
        default=False, description="Whether the persona supports multiple languages"
    )
    languages: Optional[List[Language]] = Field(
        default=None,
        description="List of languages. Required if multilingual=true.",
    )
    conversation_speed: Optional[List[ConversationSpeed]] = Field(
        default=None,
        description="Conversation speed values. Voice only.",
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
    keywords: Optional[List[str]] = Field(
        default=None, description="Free-form keywords for the persona"
    )
    # Chat settings
    tone: Optional[Tone] = Field(default=None, description="Tone. Chat only.")
    verbosity: Optional[Verbosity] = Field(
        default=None, description="Verbosity level. Chat only."
    )
    punctuation: Optional[Punctuation] = Field(
        default=None, description="Punctuation style. Chat only."
    )
    emoji_usage: Optional[EmojiUsage] = Field(
        default=None, description="Emoji usage level. Chat only."
    )
    slang_usage: Optional[SlangUsage] = Field(
        default=None, description="Slang usage level. Chat only."
    )
    typos_frequency: Optional[TypoFrequency] = Field(
        default=None, description="Typo frequency. Chat only."
    )
    regional_mix: Optional[RegionalMix] = Field(
        default=None, description="Regional language mix level. Chat only."
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None, description="Custom key-value properties for the persona"
    )
    additional_instruction: Optional[str] = Field(
        default=None, description="Additional behavior instructions for the persona"
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
class CreatePersonaTool(BaseTool):
    name = "create_persona"
    description = (
        "Creates a new workspace-level persona for simulations. "
        "Configure demographics, behavioral traits, and speech/text settings."
    )
    category = "simulation"
    input_model = CreatePersonaInput

    def execute(self, params: CreatePersonaInput, context: ToolContext) -> ToolResult:

        from simulate.models.persona import Persona

        # Cross-field validation: multilingual requires languages
        if params.multilingual and not params.languages:
            return ToolResult.error(
                "At least one language is required when multilingual is enabled.",
                error_code="VALIDATION_ERROR",
            )

        # Check for system persona with same name
        if Persona.no_workspace_objects.filter(
            name__iexact=params.name,
            persona_type=Persona.PersonaType.SYSTEM,
        ).exists():
            return ToolResult.error(
                "A system persona with this name already exists. Please choose a different name.",
                error_code="VALIDATION_ERROR",
            )

        # Check for workspace persona with same name
        if Persona.no_workspace_objects.filter(
            name__iexact=params.name,
            workspace=context.workspace,
            organization=context.organization,
            persona_type=Persona.PersonaType.WORKSPACE,
        ).exists():
            return ToolResult.error(
                f"A persona named '{params.name}' already exists in this workspace.",
                error_code="VALIDATION_ERROR",
            )

        persona = Persona(
            name=params.name,
            description=params.description,
            persona_type="workspace",
            simulation_type=params.simulation_type,
            gender=params.gender or [],
            age_group=params.age_group or [],
            occupation=params.occupation or [],
            location=params.location or [],
            personality=params.personality or [],
            communication_style=params.communication_style or [],
            accent=params.accent or [],
            multilingual=params.multilingual or False,
            languages=params.languages or [],
            conversation_speed=params.conversation_speed or [],
            background_sound=params.background_sound,
            finished_speaking_sensitivity=params.finished_speaking_sensitivity,
            interrupt_sensitivity=params.interrupt_sensitivity,
            keywords=params.keywords or [],
            tone=params.tone,
            verbosity=params.verbosity,
            punctuation=params.punctuation,
            emoji_usage=params.emoji_usage,
            slang_usage=params.slang_usage,
            typos_frequency=params.typos_frequency,
            regional_mix=params.regional_mix,
            metadata=params.metadata or {},
            additional_instruction=params.additional_instruction,
            organization=context.organization,
            workspace=context.workspace,
        )
        persona.save()

        def list_str(val):
            if val and isinstance(val, list):
                return ", ".join(str(v) for v in val)
            return "—"

        info = key_value_block(
            [
                ("ID", f"`{persona.id}`"),
                ("Name", persona.name),
                ("Type", "workspace"),
                ("Simulation Type", persona.simulation_type),
                ("Gender", list_str(persona.gender)),
                ("Personality", list_str(persona.personality)),
                ("Tone", persona.tone or "—"),
                ("Verbosity", persona.verbosity or "—"),
                ("Created", format_datetime(persona.created_at)),
            ]
        )

        content = section("Persona Created", info)

        return ToolResult(
            content=content,
            data={
                "id": str(persona.id),
                "name": persona.name,
                "simulation_type": persona.simulation_type,
                "persona_type": "workspace",
            },
        )
