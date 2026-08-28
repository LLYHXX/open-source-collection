from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class ActivateAgentVersionInput(PydanticBaseModel):
    agent_id: UUID = Field(description="The UUID of the agent definition")
    version_id: UUID = Field(description="The UUID of the version to activate")


@register_tool
class ActivateAgentVersionTool(BaseTool):
    name = "activate_agent_version"
    description = (
        "Activates a specific agent version. All other versions of the same agent "
        "are archived. Only one version can be active at a time."
    )
    category = "simulation"
    input_model = ActivateAgentVersionInput

    def execute(
        self, params: ActivateAgentVersionInput, context: ToolContext
    ) -> ToolResult:

        from simulate.models.agent_definition import AgentDefinition
        from simulate.models.agent_version import AgentVersion

        try:
            agent = AgentDefinition.objects.get(
                id=params.agent_id, organization=context.organization
            )
        except AgentDefinition.DoesNotExist:
            return ToolResult.not_found("Agent", str(params.agent_id))

        try:
            version = AgentVersion.objects.get(
                id=params.version_id, agent_definition=agent
            )
        except AgentVersion.DoesNotExist:
            return ToolResult.not_found("Agent Version", str(params.version_id))

        version.activate()

        info = key_value_block(
            [
                ("Agent", agent.agent_name),
                ("Version", version.version_name),
                ("Version Number", str(version.version_number)),
                ("Status", "active"),
            ]
        )

        content = section("Agent Version Activated", info)
        content += "\n\n_All other versions have been archived._"

        return ToolResult(
            content=content,
            data={
                "version_id": str(version.id),
                "agent_id": str(agent.id),
                "version_name": version.version_name,
                "status": "active",
            },
        )
