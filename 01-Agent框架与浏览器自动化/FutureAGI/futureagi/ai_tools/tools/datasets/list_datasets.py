from typing import Literal, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    format_datetime,
    markdown_table,
    section,
)
from ai_tools.registry import register_tool

ALLOWED_SOURCES = ("demo", "build", "observe")


class ListDatasetsInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    source: Optional[Literal["build", "demo", "observe"]] = Field(
        default=None,
        description="Filter by source: build, demo, observe",
    )
    search: Optional[str] = Field(
        default=None,
        description="Search datasets by name (case-insensitive)",
    )
    sort_by: Optional[str] = Field(
        default=None,
        description=(
            "Sort by: name, -name, created_at, -created_at, "
            "number_of_datapoints, -number_of_datapoints, "
            "number_of_experiments, -number_of_experiments "
            "(default: -created_at)"
        ),
    )


@register_tool
class ListDatasetsTool(BaseTool):
    name = "list_datasets"
    description = (
        "Lists datasets in the current workspace. "
        "Shows dataset name, source, column count, and creation time. "
        "Supports search by name, filtering by source, and sorting."
    )
    category = "datasets"
    input_model = ListDatasetsInput

    def execute(self, params: ListDatasetsInput, context: ToolContext) -> ToolResult:

        from django.db.models import Count, OuterRef, Subquery, Value
        from django.db.models.functions import Coalesce

        from model_hub.models.develop_dataset import Dataset, Row

        qs = Dataset.objects.filter(
            organization=context.organization,
            deleted=False,
            source__in=ALLOWED_SOURCES,
        ).exclude(scenarios__isnull=False)

        if params.source:
            qs = qs.filter(source=params.source)

        if params.search:
            qs = qs.filter(name__icontains=params.search)

        # Sorting — support same fields as the GetDatasetsView REST API
        sort_field = params.sort_by or "-created_at"
        simple_sorts = {"name", "-name", "created_at", "-created_at"}

        if sort_field.lstrip("-") == "number_of_datapoints":
            qs = qs.annotate(
                number_of_datapoints=Coalesce(
                    Subquery(
                        Row.objects.filter(dataset=OuterRef("pk"), deleted=False)
                        .values("dataset")
                        .annotate(count=Count("id"))
                        .values("count")[:1]
                    ),
                    Value(0),
                )
            )
        elif sort_field not in simple_sorts:
            sort_field = "-created_at"

        qs = qs.order_by(sort_field)

        total = qs.count()
        datasets = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for ds in datasets:
            col_count = len(ds.column_order) if ds.column_order else 0
            name_with_id = f"{ds.name or 'Untitled'} (`{ds.id}`)"
            rows.append(
                [
                    name_with_id,
                    ds.source or "—",
                    str(col_count),
                    format_datetime(ds.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(ds.id),
                    "name": ds.name,
                    "source": ds.source,
                    "column_count": col_count,
                }
            )

        table = markdown_table(["Name (ID)", "Source", "Columns", "Created"], rows)

        showing = f"Showing {len(rows)} of {total}"
        if params.source:
            showing += f" (filtered by source: {params.source})"
        if params.search:
            showing += f" (search: '{params.search}')"

        content = section(f"Datasets ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(content=content, data={"datasets": data_list, "total": total})
