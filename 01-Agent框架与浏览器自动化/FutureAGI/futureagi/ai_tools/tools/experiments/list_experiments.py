from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    format_datetime,
    format_status,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListExperimentsInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: not_started, running, completed, failed",
    )


@register_tool
class ListExperimentsTool(BaseTool):
    name = "list_experiments"
    description = (
        "Lists A/B experiments in the current workspace. "
        "Returns experiment name, status, dataset, variant count, and creation time."
    )
    category = "experiments"
    input_model = ListExperimentsInput

    def execute(self, params: ListExperimentsInput, context: ToolContext) -> ToolResult:

        from model_hub.models.experiments import ExperimentsTable

        qs = (
            ExperimentsTable.objects.select_related("dataset")
            .filter(
                dataset__organization=context.organization,
            )
            .order_by("-created_at")
        )

        if params.status:
            qs = qs.filter(status=params.status)

        total = qs.count()
        experiments = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for exp in experiments:
            dataset_name = exp.dataset.name if exp.dataset else "—"
            variant_count = len(exp.prompt_config) if exp.prompt_config else 0

            rows.append(
                [
                    dashboard_link(
                        "experiment",
                        str(exp.id),
                        label=f"{truncate(exp.name, 40)} (`{exp.id}`)",
                    ),
                    format_status(exp.status),
                    truncate(dataset_name, 30),
                    str(variant_count),
                    format_datetime(exp.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(exp.id),
                    "name": exp.name,
                    "status": exp.status,
                    "dataset": dataset_name,
                    "variant_count": variant_count,
                }
            )

        table = markdown_table(
            ["Name (ID)", "Status", "Dataset", "Variants", "Created"], rows
        )

        showing = f"Showing {len(rows)} of {total}"
        if params.status:
            showing += f" (status: {params.status})"

        content = section(f"Experiments ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(
            content=content, data={"experiments": data_list, "total": total}
        )
