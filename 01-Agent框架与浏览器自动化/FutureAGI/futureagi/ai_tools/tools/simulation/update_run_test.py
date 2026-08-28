from typing import List, Optional
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


class UpdateRunTestInput(PydanticBaseModel):
    run_test_id: UUID = Field(description="The UUID of the run test to update")
    name: Optional[str] = Field(default=None, description="New name")
    description: Optional[str] = Field(default=None, description="New description")
    scenario_ids: Optional[List[UUID]] = Field(
        default=None,
        description="New list of scenario UUIDs (replaces existing, at least one required)",
        min_length=1,
    )
    simulator_agent_id: Optional[UUID] = Field(
        default=None, description="New simulator agent UUID"
    )
    agent_version_id: Optional[UUID] = Field(
        default=None,
        description="UUID of the agent version to use for this test suite",
    )
    enable_tool_evaluation: Optional[bool] = Field(
        default=None,
        description="Enable or disable automatic tool evaluation for this test suite",
    )


@register_tool
class UpdateRunTestTool(BaseTool):
    name = "update_run_test"
    description = (
        "Updates an existing test suite (RunTest). "
        "Can change name, scenarios, or simulator agent."
    )
    category = "simulation"
    input_model = UpdateRunTestInput

    def execute(self, params: UpdateRunTestInput, context: ToolContext) -> ToolResult:

        from simulate.models.run_test import RunTest

        try:
            run_test = RunTest.objects.get(
                id=params.run_test_id,
                organization=context.organization,
                deleted=False,
            )
        except RunTest.DoesNotExist:
            return ToolResult.not_found("Run Test", str(params.run_test_id))

        updated_fields = []

        if params.name is not None:
            run_test.name = params.name
            updated_fields.append("name")

        if params.description is not None:
            run_test.description = params.description
            updated_fields.append("description")

        if params.simulator_agent_id is not None:
            from simulate.models.simulator_agent import SimulatorAgent

            try:
                simulator_agent = SimulatorAgent.objects.get(
                    id=params.simulator_agent_id,
                    organization=context.organization,
                )
                run_test.simulator_agent = simulator_agent
                updated_fields.append("simulator_agent")
            except SimulatorAgent.DoesNotExist:
                return ToolResult.not_found(
                    "Simulator Agent", str(params.simulator_agent_id)
                )

        if params.agent_version_id is not None:
            from simulate.models.agent_version import AgentVersion

            try:
                agent_version = AgentVersion.objects.get(
                    id=params.agent_version_id,
                    deleted=False,
                    organization=context.organization,
                )
                run_test.agent_version = agent_version
                updated_fields.append("agent_version")
            except AgentVersion.DoesNotExist:
                return ToolResult.not_found(
                    "Agent Version", str(params.agent_version_id)
                )

        if params.enable_tool_evaluation is not None:
            run_test.enable_tool_evaluation = params.enable_tool_evaluation
            updated_fields.append("enable_tool_evaluation")

        if updated_fields:
            save_fields = [
                f
                for f in updated_fields
                if f not in ("simulator_agent", "agent_version")
            ]
            if "simulator_agent" in updated_fields:
                save_fields.append("simulator_agent_id")
            if "agent_version" in updated_fields:
                save_fields.append("agent_version_id")
            run_test.save(update_fields=save_fields + ["updated_at"])

        if params.scenario_ids is not None:
            from simulate.models.scenarios import Scenarios

            scenarios = Scenarios.objects.filter(
                id__in=params.scenario_ids, organization=context.organization
            )
            if scenarios.count() != len(params.scenario_ids):
                found_ids = set(str(s.id) for s in scenarios)
                missing = [
                    str(sid) for sid in params.scenario_ids if str(sid) not in found_ids
                ]
                return ToolResult.error(
                    f"Scenarios not found: {', '.join(missing)}",
                    error_code="NOT_FOUND",
                )
            run_test.scenarios.set(scenarios)
            updated_fields.append("scenarios")

        if not updated_fields:
            return ToolResult.error(
                "No fields provided to update.",
                error_code="VALIDATION_ERROR",
            )

        info = key_value_block(
            [
                ("ID", f"`{run_test.id}`"),
                ("Name", run_test.name),
                ("Updated Fields", ", ".join(updated_fields)),
                ("Updated At", format_datetime(run_test.updated_at)),
            ]
        )

        content = section("Test Suite Updated", info)

        return ToolResult(
            content=content,
            data={
                "id": str(run_test.id),
                "name": run_test.name,
                "updated_fields": updated_fields,
            },
        )
