from uuid import UUID

from django.db import transaction
from django.utils import timezone
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool
from simulate.models import AgentVersion


class DeleteAgentDefinitionInput(PydanticBaseModel):
    agent_id: UUID = Field(description="The UUID of the agent definition to delete")


@register_tool
class DeleteAgentDefinitionTool(BaseTool):
    name = "delete_agent_definition"
    description = (
        "Soft-deletes an agent definition by marking it as deleted. "
        "The agent and its data are preserved but hidden from queries."
    )
    category = "simulation"
    input_model = DeleteAgentDefinitionInput

    def execute(
        self, params: DeleteAgentDefinitionInput, context: ToolContext
    ) -> ToolResult:
        from simulate.models.agent_definition import AgentDefinition

        try:
            agent = AgentDefinition.objects.get(
                id=params.agent_id, organization=context.organization
            )
        except AgentDefinition.DoesNotExist:
            return ToolResult.not_found("Agent", str(params.agent_id))

        with transaction.atomic():
            agent_name = agent.agent_name
            agent.delete()  # Uses BaseModel.delete() soft delete

            AgentVersion.objects.filter(
                agent_definition=agent,
                organization=agent.organization,
            ).update(deleted=True, deleted_at=timezone.now())

        info = key_value_block(
            [
                ("ID", f"`{params.agent_id}`"),
                ("Name", agent_name),
                ("Status", "Deleted"),
            ]
        )

        content = section("Agent Deleted", info)

        return ToolResult(
            content=content,
            data={"id": str(params.agent_id), "name": agent_name, "deleted": True},
        )
