from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    markdown_table,
    section,
)
from ai_tools.registry import register_tool

# Valid mapping values for voice simulations
VOICE_EVAL_COLUMNS = [
    {"field": "transcript", "name": "Transcript", "data_type": "text"},
    {"field": "voice_recording", "name": "Mono Voice Recording", "data_type": "audio"},
    {
        "field": "assistant_recording",
        "name": "Assistant Recording",
        "data_type": "audio",
    },
    {"field": "customer_recording", "name": "Customer Recording", "data_type": "audio"},
    {"field": "stereo_recording", "name": "Stereo Recording", "data_type": "audio"},
    {"field": "agent_prompt", "name": "Agent Prompt", "data_type": "text"},
]

# Valid mapping values for chat/text simulations
CHAT_EVAL_COLUMNS = [
    {"field": "transcript", "name": "Transcript", "data_type": "text"},
    {"field": "agent_prompt", "name": "Agent Prompt", "data_type": "text"},
    {
        "field": "user_chat_transcript",
        "name": "User Chat Transcript",
        "data_type": "text",
    },
    {
        "field": "assistant_chat_transcript",
        "name": "Assistant Chat Transcript",
        "data_type": "text",
    },
]

VOICE_FIELDS = {col["field"] for col in VOICE_EVAL_COLUMNS}
CHAT_FIELDS = {col["field"] for col in CHAT_EVAL_COLUMNS}
ALL_FIELDS = VOICE_FIELDS | CHAT_FIELDS


def get_valid_fields(agent_type: str) -> set:
    """Return the set of valid mapping field values for a given agent type."""
    if agent_type == "voice":
        return VOICE_FIELDS
    elif agent_type == "text":
        return CHAT_FIELDS
    return ALL_FIELDS


def auto_assign_mapping(
    required_keys: list[str],
    agent_type: str,
) -> dict[str, str]:
    """
    Auto-assign mapping for required keys based on closest semantic match.

    Uses a priority-ordered list of (keyword, field) pairs. For each required key,
    finds the best matching field from the valid columns for the agent type.
    """
    valid_fields = get_valid_fields(agent_type)

    # Priority-ordered keyword-to-field mapping rules
    keyword_rules = [
        # Audio-specific mappings
        ("audio", "voice_recording" if agent_type == "voice" else "transcript"),
        ("recording", "voice_recording"),
        ("voice", "voice_recording"),
        ("stereo", "stereo_recording"),
        ("mono", "voice_recording"),
        # Transcript mappings
        ("transcript", "transcript"),
        ("conversation", "transcript"),
        ("dialogue", "transcript"),
        ("chat", "transcript"),
        # Role-specific mappings
        (
            "assistant",
            (
                "assistant_recording"
                if agent_type == "voice"
                else "assistant_chat_transcript"
            ),
        ),
        ("agent", "agent_prompt"),
        (
            "bot",
            (
                "assistant_recording"
                if agent_type == "voice"
                else "assistant_chat_transcript"
            ),
        ),
        (
            "customer",
            "customer_recording" if agent_type == "voice" else "user_chat_transcript",
        ),
        (
            "user",
            "customer_recording" if agent_type == "voice" else "user_chat_transcript",
        ),
        # Content mappings
        ("prompt", "agent_prompt"),
        ("system_prompt", "agent_prompt"),
        ("input", "transcript"),
        ("output", "transcript"),
        ("response", "transcript"),
        ("context", "agent_prompt"),
        ("query", "transcript"),
        ("question", "transcript"),
        ("answer", "transcript"),
        ("text", "transcript"),
        ("content", "transcript"),
        ("message", "transcript"),
        ("expected_response", "transcript"),
        ("actual_response", "transcript"),
    ]

    mapping = {}
    for key in required_keys:
        key_lower = key.lower()
        matched = False

        # Try keyword matching
        for keyword, field in keyword_rules:
            if keyword in key_lower and field in valid_fields:
                mapping[key] = field
                matched = True
                break

        # Default fallback: use transcript for text keys, voice_recording for audio
        if not matched:
            mapping[key] = "transcript"

    return mapping


class ListEvalMappingOptionsInput(PydanticBaseModel):
    agent_type: Optional[str] = Field(
        default=None,
        description="Agent type to filter columns: 'voice' or 'text'. Returns all if not specified.",
    )


@register_tool
class ListEvalMappingOptionsTool(BaseTool):
    name = "list_eval_mapping_options"
    description = (
        "Lists the available mapping column options for eval configurations in simulations. "
        "These are the valid values that can be used in the 'mapping' field when configuring "
        "evaluations for run tests or prompt simulations."
    )
    category = "simulation"
    input_model = ListEvalMappingOptionsInput

    def execute(
        self, params: ListEvalMappingOptionsInput, context: ToolContext
    ) -> ToolResult:
        content = ""

        if params.agent_type != "text":
            rows = [
                [col["field"], col["name"], col["data_type"]]
                for col in VOICE_EVAL_COLUMNS
            ]
            content += section(
                "Voice Simulation Mapping Options",
                markdown_table(["Field Value", "Display Name", "Data Type"], rows),
            )

        if params.agent_type != "voice":
            rows = [
                [col["field"], col["name"], col["data_type"]]
                for col in CHAT_EVAL_COLUMNS
            ]
            content += section(
                "Chat/Text Simulation Mapping Options",
                markdown_table(["Field Value", "Display Name", "Data Type"], rows),
            )

        content += "\n\n### Usage\n\n"
        content += (
            "Use these `Field Value` entries as values in the `mapping` dict "
            "when creating eval configs. The mapping keys come from the eval template's "
            "`required_keys` (e.g., `input`, `output`, `context`, `audio`).\n\n"
            "**Example:**\n```json\n"
            '{"input": "transcript", "context": "agent_prompt", "audio": "voice_recording"}\n'
            "```"
        )

        data = {
            "voice_fields": [col["field"] for col in VOICE_EVAL_COLUMNS],
            "chat_fields": [col["field"] for col in CHAT_EVAL_COLUMNS],
        }

        return ToolResult(content=content, data=data)
