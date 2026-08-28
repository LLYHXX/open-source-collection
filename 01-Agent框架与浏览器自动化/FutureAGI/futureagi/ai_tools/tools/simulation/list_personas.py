from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListPersonasInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    persona_type: Optional[str] = Field(
        default=None, description="Filter by persona type: 'system' or 'workspace'"
    )
    simulation_type: Optional[str] = Field(
        default=None, description="Filter by simulation type: 'voice' or 'text'"
    )

    @field_validator("persona_type")
    @classmethod
    def validate_persona_type(cls, v):
        if v is not None and v not in ("system", "workspace"):
            raise ValueError(
                f"Invalid persona_type: '{v}'. Must be 'system' or 'workspace'."
            )
        return v

    @field_validator("simulation_type")
    @classmethod
    def validate_simulation_type(cls, v):
        if v is not None and v not in ("voice", "text"):
            raise ValueError(
                f"Invalid simulation_type: '{v}'. Must be 'voice' or 'text'."
            )
        return v


@register_tool
class ListPersonasTool(BaseTool):
    name = "list_personas"
    description = (
        "Lists personas available in the workspace. "
        "Includes both system-level (platform-wide) and workspace-level (user-created) personas. "
        "Filter by type or simulation mode."
    )
    category = "simulation"
    input_model = ListPersonasInput

    def execute(self, params: ListPersonasInput, context: ToolContext) -> ToolResult:
        from django.db.models import Q

        from simulate.models.persona import Persona

        # System personas have no org/workspace; workspace personas belong to the current workspace
        qs = Persona.objects.filter(
            Q(persona_type="system") | Q(workspace=context.workspace)
        ).order_by("-created_at")

        if params.persona_type:
            qs = qs.filter(persona_type=params.persona_type)
        if params.simulation_type:
            qs = qs.filter(simulation_type=params.simulation_type)

        total = qs.count()
        personas = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for p in personas:
            personality_str = ", ".join(p.personality[:2]) if p.personality else "—"
            rows.append(
                [
                    f"`{p.id}`",
                    truncate(p.name, 30),
                    p.persona_type,
                    p.simulation_type,
                    personality_str,
                    p.tone or "—",
                    format_datetime(p.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(p.id),
                    "name": p.name,
                    "persona_type": p.persona_type,
                    "simulation_type": p.simulation_type,
                }
            )

        table = markdown_table(
            ["ID", "Name", "Type", "Sim Type", "Personality", "Tone", "Created"],
            rows,
        )

        showing = f"Showing {len(rows)} of {total}"
        if params.persona_type:
            showing += f" (type: {params.persona_type})"
        if params.simulation_type:
            showing += f" (sim: {params.simulation_type})"

        content = section(f"Personas ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(content=content, data={"personas": data_list, "total": total})
