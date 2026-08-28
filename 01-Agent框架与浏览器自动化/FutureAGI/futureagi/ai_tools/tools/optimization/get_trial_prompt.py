from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_number,
    key_value_block,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetTrialPromptInput(PydanticBaseModel):
    optimization_id: UUID = Field(description="The UUID of the optimization run")
    trial_id: UUID = Field(description="The UUID of the trial")


@register_tool
class GetTrialPromptTool(BaseTool):
    name = "get_trial_prompt"
    description = (
        "Compares a trial's optimized prompt against the baseline prompt. "
        "Returns both prompts side by side to see what changed."
    )
    category = "optimization"
    input_model = GetTrialPromptInput

    def execute(self, params: GetTrialPromptInput, context: ToolContext) -> ToolResult:

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

        # Get baseline
        baseline = DatasetOptimizationTrial.objects.filter(
            optimization_run=run, is_baseline=True
        ).first()

        baseline_prompt = baseline.prompt if baseline else "—"
        trial_prompt = trial.prompt or "—"

        # Calculate improvement
        pct_change = None
        if (
            trial.average_score is not None
            and baseline
            and baseline.average_score
            and baseline.average_score > 0
        ):
            pct_change = (
                (trial.average_score - baseline.average_score) / baseline.average_score
            ) * 100

        trial_label = "Baseline" if trial.is_baseline else f"Trial {trial.trial_number}"

        info = key_value_block(
            [
                ("Run", run.name),
                ("Trial", trial_label),
                (
                    "Trial Score",
                    (
                        format_number(trial.average_score)
                        if trial.average_score is not None
                        else "—"
                    ),
                ),
                (
                    "Baseline Score",
                    (
                        format_number(baseline.average_score)
                        if baseline and baseline.average_score is not None
                        else "—"
                    ),
                ),
                (
                    "Improvement",
                    f"{pct_change:+.2f}%" if pct_change is not None else "—",
                ),
            ]
        )

        content = section(f"Prompt Comparison: {trial_label}", info)
        content += (
            f"\n\n### Baseline Prompt\n\n```\n{truncate(baseline_prompt, 800)}\n```"
        )
        content += f"\n\n### Trial Prompt\n\n```\n{truncate(trial_prompt, 800)}\n```"

        return ToolResult(
            content=content,
            data={
                "baseline_prompt": baseline_prompt,
                "trial_prompt": trial_prompt,
                "baseline_score": (
                    float(baseline.average_score)
                    if baseline and baseline.average_score is not None
                    else None
                ),
                "trial_score": (
                    float(trial.average_score)
                    if trial.average_score is not None
                    else None
                ),
            },
        )
