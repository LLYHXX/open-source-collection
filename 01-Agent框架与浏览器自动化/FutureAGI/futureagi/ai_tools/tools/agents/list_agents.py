import re
from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    format_datetime,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListAgentsInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    agent_type: Optional[str] = Field(
        default=None, description="Filter by agent type: voice or text"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search agents by name, description, or contact number",
    )


@register_tool
class ListAgentsTool(BaseTool):
    name = "list_agents"
    description = (
        "Lists agent definitions in the current workspace. "
        "Shows agent name, type, provider, and creation time."
    )
    category = "agents"
    input_model = ListAgentsInput

    def execute(self, params: ListAgentsInput, context: ToolContext) -> ToolResult:

        from django.db.models import OuterRef, Subquery

        from simulate.models.agent_definition import AgentDefinition
        from simulate.models.agent_version import AgentVersion

        # Annotate with latest version number (avoid N+1)
        latest_version_subquery = (
            AgentVersion.objects.filter(
                agent_definition=OuterRef("pk"), status="active"
            )
            .order_by("-version_number")
            .values("version_number")[:1]
        )

        qs = (
            AgentDefinition.objects.filter(
                organization=context.organization,
            )
            .annotate(
                _active_version=Subquery(latest_version_subquery),
            )
            .order_by("-created_at")
        )

        if params.agent_type:
            if params.agent_type not in [
                choice[0] for choice in AgentDefinition.AgentTypeChoices.choices
            ]:
                return ToolResult.bad_param("agent_type", "Invalid agent type")
            qs = qs.filter(agent_type=params.agent_type)

        if params.search:
            from django.db import models

            # Create case-insensitive regex pattern for search
            pattern = rf"(?i){re.escape(params.search)}"
            qs = qs.filter(
                models.Q(agent_name__regex=pattern)
                | models.Q(description__regex=pattern)
                | models.Q(contact_number__regex=pattern)
                | models.Q(assistant_id__regex=pattern)
            )

        total = qs.count()
        agents = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for agent in agents:
            version_str = str(agent._active_version) if agent._active_version else "—"
            rows.append(
                [
                    dashboard_link(
                        "agent",
                        str(agent.id),
                        label=f"{truncate(agent.agent_name, 40)} (`{agent.id}`)",
                    ),
                    agent.agent_type,
                    agent.provider or "—",
                    agent.model or "—",
                    f"v{version_str}" if agent._active_version else "—",
                    format_datetime(agent.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(agent.id),
                    "name": agent.agent_name,
                    "type": agent.agent_type,
                    "provider": agent.provider,
                    "model": agent.model,
                    "active_version": agent._active_version,
                }
            )

        table = markdown_table(
            ["Name (ID)", "Type", "Provider", "Model", "Version", "Created"], rows
        )

        showing = f"Showing {len(rows)} of {total}"
        if params.agent_type:
            showing += f" (type: {params.agent_type})"
        if params.search:
            showing += f" (search: {params.search})"

        content = section(f"Agents ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(content=content, data={"agents": data_list, "total": total})
