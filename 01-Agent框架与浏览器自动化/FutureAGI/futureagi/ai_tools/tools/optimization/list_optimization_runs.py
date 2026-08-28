from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    format_number,
    format_status,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListOptimizationRunsInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: not_started, pending, running, completed, failed, cancelled",
    )
    dataset_id: Optional[UUID] = Field(
        default=None, description="Filter by source dataset ID"
    )


@register_tool
class ListOptimizationRunsTool(BaseTool):
    name = "list_optimization_runs"
    description = (
        "Lists prompt optimization runs in the workspace. "
        "Prompt optimization tests different prompt variants to find the best one. "
        "Supports 6 algorithms: random_search, bayesian, metaprompt, protegi, "
        "promptwizard, gepa. Returns run name, algorithm, status, best score, "
        "and trial count."
    )
    category = "optimization"
    input_model = ListOptimizationRunsInput

    def execute(
        self, params: ListOptimizationRunsInput, context: ToolContext
    ) -> ToolResult:
        from django.db.models import Count

        from model_hub.models.optimize_dataset import OptimizeDataset

        qs = OptimizeDataset.objects.annotate(trial_count=Count("trials")).order_by(
            "-created_at"
        )

        if params.status:
            qs = qs.filter(status=params.status)
        if params.dataset_id:
            # Filter through the column's dataset
            qs = qs.filter(column__dataset_id=params.dataset_id)

        total = qs.count()
        runs = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for run in runs:
            algo = run.optimizer_algorithm or "—"
            best = format_number(run.best_score) if run.best_score is not None else "—"
            baseline = (
                format_number(run.baseline_score)
                if run.baseline_score is not None
                else "—"
            )

            rows.append(
                [
                    f"`{run.id}`",
                    truncate(run.name, 35),
                    algo,
                    format_status(run.status),
                    str(run.trial_count),
                    baseline,
                    best,
                    format_datetime(run.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(run.id),
                    "name": run.name,
                    "algorithm": algo,
                    "status": run.status,
                    "trial_count": run.trial_count,
                    "best_score": (
                        float(run.best_score) if run.best_score is not None else None
                    ),
                    "baseline_score": (
                        float(run.baseline_score)
                        if run.baseline_score is not None
                        else None
                    ),
                }
            )

        table = markdown_table(
            [
                "ID",
                "Name",
                "Algorithm",
                "Status",
                "Trials",
                "Baseline",
                "Best",
                "Created",
            ],
            rows,
        )

        showing = f"Showing {len(rows)} of {total}"
        if params.status:
            showing += f" (status: {params.status})"

        content = section(f"Optimization Runs ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(content=content, data={"runs": data_list, "total": total})
