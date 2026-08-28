from typing import Optional
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


class UpdateSimulatorAgentInput(PydanticBaseModel):
    simulator_agent_id: UUID = Field(
        description="The UUID of the simulator agent to update"
    )
    name: Optional[str] = Field(default=None, description="New name")
    prompt: Optional[str] = Field(default=None, description="New system prompt")
    voice_provider: Optional[str] = Field(
        default=None, description="New voice provider"
    )
    voice_name: Optional[str] = Field(default=None, description="New voice name")
    model: Optional[str] = Field(default=None, description="New LLM model")
    llm_temperature: Optional[float] = Field(
        default=None, ge=0.0, le=2.0, description="New temperature"
    )
    max_call_duration_in_minutes: Optional[int] = Field(
        default=None, ge=1, le=180, description="New max duration"
    )
    interrupt_sensitivity: Optional[float] = Field(
        default=None, ge=0.0, le=11.0, description="New interrupt sensitivity"
    )
    conversation_speed: Optional[float] = Field(
        default=None, ge=0.1, le=2.0, description="New conversation speed"
    )


@register_tool
class UpdateSimulatorAgentTool(BaseTool):
    name = "update_simulator_agent"
    description = "Updates an existing simulator agent configuration. Only provided fields will be changed."
    category = "simulation"
    input_model = UpdateSimulatorAgentInput

    def execute(
        self, params: UpdateSimulatorAgentInput, context: ToolContext
    ) -> ToolResult:

        from simulate.models.simulator_agent import SimulatorAgent

        try:
            sa = SimulatorAgent.objects.get(
                id=params.simulator_agent_id, organization=context.organization
            )
        except SimulatorAgent.DoesNotExist:
            return ToolResult.not_found(
                "Simulator Agent", str(params.simulator_agent_id)
            )

        updated_fields = []
        field_map = {
            "name": params.name,
            "prompt": params.prompt,
            "voice_provider": params.voice_provider,
            "voice_name": params.voice_name,
            "model": params.model,
            "llm_temperature": params.llm_temperature,
            "max_call_duration_in_minutes": params.max_call_duration_in_minutes,
            "interrupt_sensitivity": params.interrupt_sensitivity,
            "conversation_speed": params.conversation_speed,
        }

        for field_name, value in field_map.items():
            if value is not None:
                setattr(sa, field_name, value)
                updated_fields.append(field_name)

        if not updated_fields:
            return ToolResult.error(
                "No fields provided to update.",
                error_code="VALIDATION_ERROR",
            )

        sa.save(update_fields=updated_fields + ["updated_at"])

        info = key_value_block(
            [
                ("ID", f"`{sa.id}`"),
                ("Name", sa.name),
                ("Updated Fields", ", ".join(updated_fields)),
                ("Updated At", format_datetime(sa.updated_at)),
            ]
        )

        content = section("Simulator Agent Updated", info)

        return ToolResult(
            content=content,
            data={
                "id": str(sa.id),
                "name": sa.name,
                "updated_fields": updated_fields,
            },
        )
