from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import section
from ai_tools.registry import register_tool


class DeletePromptSimulationInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template")
    simulation_id: UUID = Field(description="The UUID of the simulation run to delete")


@register_tool
class DeletePromptSimulationTool(BaseTool):
    name = "delete_prompt_simulation"
    description = (
        "Soft-deletes a prompt simulation run. "
        "The simulation and its executions will no longer appear in listings."
    )
    category = "prompts"
    input_model = DeletePromptSimulationInput

    def execute(
        self, params: DeletePromptSimulationInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.run_prompt import PromptTemplate
        from simulate.models import RunTest

        try:
            template = PromptTemplate.objects.get(
                id=params.template_id,
                organization=context.organization,
                deleted=False,
            )
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        try:
            sim = RunTest.objects.get(
                id=params.simulation_id,
                prompt_template=template,
                source_type="prompt",
                organization=context.organization,
                deleted=False,
            )
        except RunTest.DoesNotExist:
            return ToolResult.not_found("Simulation", str(params.simulation_id))

        sim.delete()

        return ToolResult(
            content=section(
                "Simulation Deleted",
                f"Prompt simulation **{sim.name}** has been deleted.",
            ),
            data={"simulation_id": str(sim.id), "name": sim.name},
        )
