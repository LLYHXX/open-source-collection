from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListPromptScenariosInput(PydanticBaseModel):
    search: Optional[str] = Field(default=None, description="Search by scenario name")
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


@register_tool
class ListPromptScenariosTool(BaseTool):
    name = "list_prompt_scenarios"
    description = (
        "Lists available scenarios for prompt simulations. "
        "Scenarios define test inputs (datasets or scripts) that prompts are executed against."
    )
    category = "prompts"
    input_model = ListPromptScenariosInput

    def execute(
        self, params: ListPromptScenariosInput, context: ToolContext
    ) -> ToolResult:

        from simulate.models import Scenarios

        qs = Scenarios.objects.filter(
            organization=context.organization,
            deleted=False,
        ).order_by("-created_at")

        if params.search:
            qs = qs.filter(name__icontains=params.search)

        total = qs.count()
        scenarios = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for s in scenarios:
            rows.append(
                [
                    f"`{s.id}`",
                    truncate(s.name, 40),
                    s.scenario_type,
                    s.source_type or "—",
                    str(s.dataset_id) if s.dataset_id else "—",
                    format_datetime(s.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(s.id),
                    "name": s.name,
                    "scenario_type": s.scenario_type,
                    "source_type": s.source_type,
                    "dataset_id": str(s.dataset_id) if s.dataset_id else None,
                }
            )

        table = markdown_table(
            ["ID", "Name", "Type", "Source", "Dataset", "Created"],
            rows,
        )

        showing = f"Showing {len(rows)} of {total}"
        content = section(f"Prompt Scenarios ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += f"\n\n_Use offset={params.offset + params.limit} to see more._"

        return ToolResult(
            content=content, data={"scenarios": data_list, "total": total}
        )
