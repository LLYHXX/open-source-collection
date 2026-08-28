from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DeleteScenarioInput(PydanticBaseModel):
    scenario_id: UUID = Field(description="The UUID of the scenario to delete")


@register_tool
class DeleteScenarioTool(BaseTool):
    name = "delete_scenario"
    description = "Soft-deletes a test scenario by marking it as deleted."
    category = "simulation"
    input_model = DeleteScenarioInput

    def execute(self, params: DeleteScenarioInput, context: ToolContext) -> ToolResult:
        from django.utils import timezone

        from simulate.models.scenarios import Scenarios

        try:
            scenario = Scenarios.objects.get(
                id=params.scenario_id,
                organization=context.organization,
                deleted=False,
            )
        except Scenarios.DoesNotExist:
            return ToolResult.not_found("Scenario", str(params.scenario_id))

        scenario_name = scenario.name
        scenario.deleted = True
        scenario.deleted_at = timezone.now()
        scenario.save(update_fields=["deleted", "deleted_at", "updated_at"])

        info = key_value_block(
            [
                ("ID", f"`{params.scenario_id}`"),
                ("Name", scenario_name),
                ("Status", "Deleted"),
            ]
        )

        content = section("Scenario Deleted", info)

        return ToolResult(
            content=content,
            data={
                "id": str(params.scenario_id),
                "name": scenario_name,
                "deleted": True,
            },
        )
