from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    format_status,
    key_value_block,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetOptimizationStepsInput(PydanticBaseModel):
    optimization_id: UUID = Field(description="The UUID of the optimization run")


@register_tool
class GetOptimizationStepsTool(BaseTool):
    name = "get_optimization_steps"
    description = (
        "Returns the step-by-step progress of an optimization run. "
        "Shows 4 stages: initialization, baseline eval, optimization trials, "
        "and finalization — each with status and timestamps."
    )
    category = "optimization"
    input_model = GetOptimizationStepsInput

    def execute(
        self, params: GetOptimizationStepsInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.dataset_optimization_step import DatasetOptimizationStep
        from model_hub.models.optimize_dataset import OptimizeDataset

        try:
            run = OptimizeDataset.objects.get(id=params.optimization_id)
        except OptimizeDataset.DoesNotExist:
            return ToolResult.not_found("Optimization Run", str(params.optimization_id))

        steps = DatasetOptimizationStep.objects.filter(optimization_run=run).order_by(
            "step_number"
        )

        if not steps.exists():
            return ToolResult(
                content=section(
                    f"Optimization Steps: {run.name}",
                    "_No steps found. The optimization may not have started yet._",
                ),
                data={"steps": []},
            )

        rows = []
        data_list = []
        for s in steps:
            rows.append(
                [
                    str(s.step_number),
                    s.name or "—",
                    format_status(s.status),
                    truncate(s.description, 50) if s.description else "—",
                    format_datetime(s.updated_at),
                ]
            )
            data_list.append(
                {
                    "step_number": s.step_number,
                    "name": s.name,
                    "status": s.status,
                    "description": s.description,
                }
            )

        table = markdown_table(
            ["Step", "Name", "Status", "Description", "Updated"],
            rows,
        )

        info = key_value_block(
            [
                ("Run", run.name),
                ("Overall Status", format_status(run.status)),
                ("Algorithm", run.optimizer_algorithm or "—"),
            ]
        )

        content = section(f"Optimization Steps: {run.name}", info)
        content += f"\n\n{table}"

        return ToolResult(
            content=content,
            data={"steps": data_list, "run_status": run.status},
        )
