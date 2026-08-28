from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_number,
    key_value_block,
    markdown_table,
    section,
)
from ai_tools.registry import register_tool


class GetTrialEvaluationsInput(PydanticBaseModel):
    optimization_id: UUID = Field(description="The UUID of the optimization run")
    trial_id: UUID = Field(description="The UUID of the trial")


@register_tool
class GetTrialEvaluationsTool(BaseTool):
    name = "get_trial_evaluations"
    description = (
        "Returns per-metric evaluation breakdown for a specific optimization trial. "
        "Shows each eval metric's average score and percentage change from baseline."
    )
    category = "optimization"
    input_model = GetTrialEvaluationsInput

    def execute(
        self, params: GetTrialEvaluationsInput, context: ToolContext
    ) -> ToolResult:
        from django.db.models import Avg

        from model_hub.models.dataset_optimization_trial import DatasetOptimizationTrial
        from model_hub.models.dataset_optimization_trial_item import (
            DatasetOptimizationItemEvaluation,
            DatasetOptimizationTrialItem,
        )
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

        # Get baseline for comparison
        baseline = DatasetOptimizationTrial.objects.filter(
            optimization_run=run, is_baseline=True
        ).first()

        # Get evaluations for this trial
        trial_items = DatasetOptimizationTrialItem.objects.filter(trial=trial)
        item_ids = list(trial_items.values_list("id", flat=True))

        evals = DatasetOptimizationItemEvaluation.objects.filter(
            trial_item_id__in=item_ids
        ).select_related("eval_metric")

        # Aggregate by eval metric
        metric_scores = {}  # eval_metric_id -> {name, scores}
        for ev in evals:
            mid = str(ev.eval_metric_id)
            if mid not in metric_scores:
                metric_scores[mid] = {
                    "name": ev.eval_metric.name if ev.eval_metric else "—",
                    "scores": [],
                }
            if ev.score is not None:
                metric_scores[mid]["scores"].append(float(ev.score))

        # Get baseline metric scores for comparison
        baseline_metric_scores = {}
        if baseline and not trial.is_baseline:
            baseline_items = DatasetOptimizationTrialItem.objects.filter(trial=baseline)
            baseline_item_ids = list(baseline_items.values_list("id", flat=True))
            baseline_evals = DatasetOptimizationItemEvaluation.objects.filter(
                trial_item_id__in=baseline_item_ids
            )
            for ev in baseline_evals:
                mid = str(ev.eval_metric_id)
                if mid not in baseline_metric_scores:
                    baseline_metric_scores[mid] = []
                if ev.score is not None:
                    baseline_metric_scores[mid].append(float(ev.score))

        rows = []
        data_list = []
        for mid, info in metric_scores.items():
            avg_score = (
                sum(info["scores"]) / len(info["scores"]) if info["scores"] else None
            )

            # Calculate change
            pct_change = None
            baseline_avg = None
            if mid in baseline_metric_scores and baseline_metric_scores[mid]:
                baseline_avg = sum(baseline_metric_scores[mid]) / len(
                    baseline_metric_scores[mid]
                )
                if baseline_avg and baseline_avg > 0 and avg_score is not None:
                    pct_change = ((avg_score - baseline_avg) / baseline_avg) * 100

            rows.append(
                [
                    info["name"],
                    format_number(avg_score) if avg_score is not None else "—",
                    format_number(baseline_avg) if baseline_avg is not None else "—",
                    f"{pct_change:+.1f}%" if pct_change is not None else "—",
                ]
            )
            data_list.append(
                {
                    "eval_metric_id": mid,
                    "name": info["name"],
                    "avg_score": avg_score,
                    "baseline_score": baseline_avg,
                    "pct_change": (
                        round(pct_change, 2) if pct_change is not None else None
                    ),
                }
            )

        if not rows:
            trial_label = (
                "Baseline" if trial.is_baseline else f"Trial {trial.trial_number}"
            )
            return ToolResult(
                content=section(
                    f"Trial Evaluations: {trial_label}",
                    "_No per-metric evaluation data found._",
                ),
                data={"evaluations": []},
            )

        table = markdown_table(
            ["Metric", "Trial Score", "Baseline Score", "Change"],
            rows,
        )

        trial_label = "Baseline" if trial.is_baseline else f"Trial {trial.trial_number}"
        info_block = key_value_block(
            [
                ("Run", run.name),
                ("Trial", trial_label),
                (
                    "Overall Score",
                    (
                        format_number(trial.average_score)
                        if trial.average_score is not None
                        else "—"
                    ),
                ),
                ("Metrics", str(len(data_list))),
            ]
        )

        content = section(f"Trial Evaluations: {trial_label}", info_block)
        content += f"\n\n{table}"

        return ToolResult(
            content=content,
            data={"evaluations": data_list},
        )
