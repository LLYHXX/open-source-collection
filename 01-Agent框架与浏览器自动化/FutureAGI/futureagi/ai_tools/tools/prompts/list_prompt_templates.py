from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    format_datetime,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListPromptTemplatesInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    search: Optional[str] = Field(default=None, description="Search by template name")
    folder_id: Optional[str] = Field(default=None, description="Filter by folder UUID")


@register_tool
class ListPromptTemplatesTool(BaseTool):
    name = "list_prompt_templates"
    description = (
        "Lists prompt templates in the workspace. "
        "Returns template name, version count, folder, variables, and creation date. "
        "Use get_prompt_template for full details of a specific template."
    )
    category = "prompts"
    input_model = ListPromptTemplatesInput

    def execute(
        self, params: ListPromptTemplatesInput, context: ToolContext
    ) -> ToolResult:
        from django.db.models import Count, Q

        from model_hub.models.run_prompt import PromptTemplate, PromptVersion

        qs = (
            PromptTemplate.objects.all()
            .annotate(
                version_count=Count(
                    "all_executions",
                    filter=Q(all_executions__deleted=False),
                )
            )
            .order_by("-updated_at")
        )

        if params.search:
            qs = qs.filter(name__icontains=params.search)
        if params.folder_id:
            qs = qs.filter(prompt_folder_id=params.folder_id)

        total = qs.count()
        templates = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for t in templates:
            # Get default version info
            default_ver = PromptVersion.objects.filter(
                original_template=t, deleted=False, is_default=True
            ).first()
            ver_label = default_ver.template_version if default_ver else "—"

            folder_name = t.prompt_folder.name if t.prompt_folder else "—"
            var_names = t.variable_names
            # variable_names can be a list or dict; normalize to list
            if isinstance(var_names, dict):
                var_names = list(var_names.keys())
            elif not isinstance(var_names, list):
                var_names = []
            vars_str = ", ".join(var_names[:3]) if var_names else "—"
            if var_names and len(var_names) > 3:
                vars_str += f" (+{len(var_names) - 3})"

            rows.append(
                [
                    f"[`{t.id}`]({dashboard_link('prompt_template', t.id, context.workspace)})",
                    truncate(t.name, 40),
                    ver_label,
                    str(t.version_count),
                    folder_name,
                    vars_str,
                    format_datetime(t.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "default_version": ver_label,
                    "version_count": t.version_count,
                    "folder": folder_name,
                    "variable_names": t.variable_names or [],
                }
            )

        table = markdown_table(
            ["ID", "Name", "Default Ver", "Versions", "Folder", "Variables", "Created"],
            rows,
        )

        showing = f"Showing {len(rows)} of {total}"
        content = section(f"Prompt Templates ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += f"\n\n_Use offset={params.offset + params.limit} to see more._"

        return ToolResult(
            content=content, data={"templates": data_list, "total": total}
        )
