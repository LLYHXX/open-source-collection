from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_status,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class ExecutePromptSimulationInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template")
    simulation_id: UUID = Field(
        description="The UUID of the simulation run (RunTest) to execute"
    )
    scenario_ids: Optional[List[UUID]] = Field(
        default=None,
        description=(
            "Optional list of specific scenario UUIDs to execute. "
            "If omitted, all scenarios configured in the simulation are used."
        ),
    )
    select_all: bool = Field(
        default=False,
        description=(
            "If true with scenario_ids, run all scenarios EXCEPT those IDs. "
            "If true without scenario_ids, run all scenarios."
        ),
    )


@register_tool
class ExecutePromptSimulationTool(BaseTool):
    name = "execute_prompt_simulation"
    description = (
        "Triggers execution of a prompt simulation run. "
        "Creates a TestExecution and starts the simulation workflow. "
        "Returns the execution ID for tracking."
    )
    category = "prompts"
    input_model = ExecutePromptSimulationInput

    def execute(
        self, params: ExecutePromptSimulationInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.run_prompt import PromptTemplate
        from simulate.models import RunTest
        from simulate.services.test_executor import TestExecutor

        # Validate template exists and belongs to org
        try:
            template = PromptTemplate.objects.get(
                id=params.template_id,
                organization=context.organization,
                deleted=False,
            )
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        # Validate simulation exists
        try:
            run_test = RunTest.objects.get(
                id=params.simulation_id,
                prompt_template=template,
                source_type="prompt",
                organization=context.organization,
                deleted=False,
            )
        except RunTest.DoesNotExist:
            return ToolResult.not_found("Simulation", str(params.simulation_id))

        # Validate prompt version still exists and is not deleted
        if not run_test.prompt_version or run_test.prompt_version.deleted:
            return ToolResult.validation_error(
                "Prompt version has been deleted. "
                "Please update the simulation with a valid version."
            )

        # Get all available scenario IDs linked to this run test (not deleted)
        all_scenario_ids = list(
            run_test.scenarios.filter(deleted=False).values_list("id", flat=True)
        )

        # Determine which scenarios to execute
        if params.select_all:
            if params.scenario_ids:
                exclude_set = {str(sid) for sid in params.scenario_ids}
                final_scenario_ids = [
                    str(sid) for sid in all_scenario_ids if str(sid) not in exclude_set
                ]
            else:
                final_scenario_ids = [str(sid) for sid in all_scenario_ids]
        else:
            if params.scenario_ids:
                final_scenario_ids = [str(sid) for sid in params.scenario_ids]
            else:
                final_scenario_ids = [str(sid) for sid in all_scenario_ids]

        if not final_scenario_ids:
            return ToolResult.validation_error(
                "No valid scenarios available for execution. "
                "Please add at least one scenario to the simulation."
            )

        test_executor = TestExecutor()
        result = test_executor.execute_test(
            run_test_id=str(run_test.id),
            user_id=str(context.user_id),
            scenario_ids=final_scenario_ids,
            simulator_id=None,
        )

        if not result["success"]:
            return ToolResult.error(
                result.get("error", "Failed to start simulation execution"),
                error_code="EXECUTION_ERROR",
            )

        info = key_value_block(
            [
                ("Execution ID", f"`{result['execution_id']}`"),
                ("Simulation", run_test.name),
                ("Template", template.name),
                (
                    "Scenarios",
                    str(result.get("total_scenarios", len(final_scenario_ids))),
                ),
                ("Status", format_status(result.get("status", "pending"))),
            ]
        )

        content = section("Prompt Simulation Started", info)
        content += "\n\n_Simulation is running asynchronously. Use `get_prompt_simulation` to check status._"

        return ToolResult(
            content=content,
            data={
                "execution_id": result["execution_id"],
                "run_test_id": str(run_test.id),
                "template_id": str(template.id),
                "scenarios": len(final_scenario_ids),
                "status": result.get("status", "pending"),
            },
        )
