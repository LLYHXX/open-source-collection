from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListSimulatorAgentsInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


@register_tool
class ListSimulatorAgentsTool(BaseTool):
    name = "list_simulator_agents"
    description = (
        "Lists simulator agents (bot configurations) in the workspace. "
        "Simulator agents define the bot behavior for test simulations."
    )
    category = "simulation"
    input_model = ListSimulatorAgentsInput

    def execute(
        self, params: ListSimulatorAgentsInput, context: ToolContext
    ) -> ToolResult:

        from simulate.models.simulator_agent import SimulatorAgent

        qs = SimulatorAgent.objects.filter(organization=context.organization).order_by(
            "-created_at"
        )

        total = qs.count()
        agents = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for sa in agents:
            rows.append(
                [
                    f"`{sa.id}`",
                    truncate(sa.name, 30),
                    sa.model or "—",
                    sa.voice_provider or "—",
                    sa.voice_name or "—",
                    f"{sa.llm_temperature}",
                    f"{sa.max_call_duration_in_minutes}m",
                    format_datetime(sa.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(sa.id),
                    "name": sa.name,
                    "model": sa.model,
                    "voice_provider": sa.voice_provider,
                    "voice_name": sa.voice_name,
                }
            )

        table = markdown_table(
            [
                "ID",
                "Name",
                "Model",
                "Voice Provider",
                "Voice",
                "Temperature",
                "Max Duration",
                "Created",
            ],
            rows,
        )

        content = section(
            f"Simulator Agents ({total})",
            f"Showing {len(rows)} of {total}\n\n{table}",
        )

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(
            content=content, data={"simulator_agents": data_list, "total": total}
        )
