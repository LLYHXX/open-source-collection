from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    markdown_table,
    section,
)
from ai_tools.registry import register_tool


class ListPromptLabelsInput(PydanticBaseModel):
    limit: int = Field(default=50, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


@register_tool
class ListPromptLabelsTool(BaseTool):
    name = "list_prompt_labels"
    description = (
        "Lists prompt labels available in the workspace. "
        "Labels like Production, Staging, Development can be assigned to prompt versions "
        "to track deployment status."
    )
    category = "prompts"
    input_model = ListPromptLabelsInput

    def execute(
        self, params: ListPromptLabelsInput, context: ToolContext
    ) -> ToolResult:

        from django.db.models import Q

        from model_hub.models.prompt_label import PromptLabel

        qs = PromptLabel.no_workspace_objects.filter(
            Q(organization=context.organization, workspace=context.workspace)
            | Q(organization__isnull=True, type="system"),
            deleted=False,
        ).order_by("name")
        total = qs.count()
        labels = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for label in labels:
            is_system = label.type == "system"
            rows.append(
                [
                    f"`{label.id}`",
                    label.name,
                    "System" if is_system else "Custom",
                    format_datetime(label.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(label.id),
                    "name": label.name,
                    "is_system": is_system,
                }
            )

        table = markdown_table(["ID", "Name", "Type", "Created"], rows)

        showing = f"Showing {len(rows)} of {total}"
        content = section(f"Prompt Labels ({total})", f"{showing}\n\n{table}")

        return ToolResult(content=content, data={"labels": data_list, "total": total})
