from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    format_number,
    key_value_block,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetOptimizationTrialInput(PydanticBaseModel):
    optimization_id: UUID = Field(description="The UUID of the optimization run")
    trial_id: UUID = Field(description="The UUID of the trial")


@register_tool
class GetOptimizationTrialTool(BaseTool):
    name = "get_optimization_trial"
    description = (
        "Returns detailed information about a specific optimization trial including "
        "its prompt, score, percentage change from baseline, and creation time."
    )
    category = "optimization"
    input_model = GetOptimizationTrialInput

    def execute(
        self, params: GetOptimizationTrialInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.dataset_optimization_trial import DatasetOptimizationTrial
        from model_hub.models.optimize_dataset import OptimizeDataset

        try:
            run = OptimizeDataset.objects.get(id=params.optimization_id)
        except OptimizeDataset.DoesNotExist:
            return ToolResult.not_found("Optimization Run", str(params.optimization_id))

        try:
            trial = DatasetOptimizationTrial.objects.get(
                id=params.trial_id, optimization_run=run
            )
        except DatasetOptimizationTrial.DoesNotExist:
            return ToolResult.not_found("Trial", str(params.trial_id))

        # Calculate percentage change
        pct_change = None
        if (
            trial.average_score is not None
            and run.baseline_score
            and run.baseline_score > 0
        ):
            pct_change = (
                (trial.average_score - run.baseline_score) / run.baseline_score
            ) * 100

        trial_label = "Baseline" if trial.is_baseline else f"Trial {trial.trial_number}"

        info = key_value_block(
            [
                ("Run", run.name),
                ("Trial", trial_label),
                ("Trial ID", f"`{trial.id}`"),
                (
                    "Score",
                    (
                        format_number(trial.average_score)
                        if trial.average_score is not None
                        else "—"
                    ),
                ),
                (
                    "Change vs Baseline",
                    f"{pct_change:+.2f}%" if pct_change is not None else "—",
                ),
                ("Is Baseline", "Yes" if trial.is_baseline else "No"),
                ("Created", format_datetime(trial.created_at)),
            ]
        )

        content = section(f"Trial: {trial_label}", info)

        if trial.prompt:
            content += f"\n\n### Prompt\n\n```\n{truncate(trial.prompt, 1000)}\n```"

        return ToolResult(
            content=content,
            data={
                "trial_id": str(trial.id),
                "trial_number": trial.trial_number,
                "is_baseline": trial.is_baseline,
                "score": (
                    float(trial.average_score)
                    if trial.average_score is not None
                    else None
                ),
                "pct_change": round(pct_change, 2) if pct_change is not None else None,
                "prompt": trial.prompt,
            },
        )
