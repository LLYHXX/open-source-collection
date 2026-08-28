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


class ListPromptFoldersInput(PydanticBaseModel):
    limit: int = Field(default=50, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


@register_tool
class ListPromptFoldersTool(BaseTool):
    name = "list_prompt_folders"
    description = (
        "Lists prompt folders in the workspace. "
        "Folders organize prompt templates into hierarchical groups."
    )
    category = "prompts"
    input_model = ListPromptFoldersInput

    def execute(
        self, params: ListPromptFoldersInput, context: ToolContext
    ) -> ToolResult:
        from django.db.models import Count, Q

        from model_hub.models.prompt_folders import PromptFolder

        qs = (
            PromptFolder.no_workspace_objects.filter(
                Q(workspace=context.workspace, organization=context.organization)
                | Q(is_sample=True),
                deleted=False,
            )
            .annotate(
                template_count=Count(
                    "prompt_templates",
                    filter=Q(prompt_templates__deleted=False),
                )
            )
            .order_by("name")
        )

        total = qs.count()
        folders = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for f in folders:
            parent_name = "—"
            if hasattr(f, "parent_folder") and f.parent_folder:
                parent_name = f.parent_folder.name

            rows.append(
                [
                    f"`{f.id}`",
                    truncate(f.name, 40),
                    parent_name,
                    str(f.template_count),
                    format_datetime(f.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(f.id),
                    "name": f.name,
                    "parent": parent_name,
                    "template_count": f.template_count,
                }
            )

        table = markdown_table(["ID", "Name", "Parent", "Templates", "Created"], rows)

        showing = f"Showing {len(rows)} of {total}"
        content = section(f"Prompt Folders ({total})", f"{showing}\n\n{table}")

        return ToolResult(content=content, data={"folders": data_list, "total": total})
