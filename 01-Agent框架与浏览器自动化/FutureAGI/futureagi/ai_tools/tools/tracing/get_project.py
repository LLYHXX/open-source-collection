from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    format_datetime,
    key_value_block,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetProjectInput(PydanticBaseModel):
    project_id: UUID = Field(description="The UUID of the project to retrieve")
    include_versions: bool = Field(
        default=True, description="Include project versions in the response"
    )


@register_tool
class GetProjectTool(BaseTool):
    name = "get_project"
    description = (
        "Returns detailed information about a tracing project including "
        "its versions, trace count, configuration, and metadata."
    )
    category = "tracing"
    input_model = GetProjectInput

    def execute(self, params: GetProjectInput, context: ToolContext) -> ToolResult:
        from django.db.models import Count

        from tracer.models.project import Project
        from tracer.models.project_version import ProjectVersion

        try:
            project = Project.objects.annotate(trace_count=Count("traces")).get(
                id=params.project_id, organization=context.organization
            )
        except Project.DoesNotExist:
            return ToolResult.not_found("Project", str(params.project_id))

        info = key_value_block(
            [
                ("ID", f"`{project.id}`"),
                ("Name", project.name),
                ("Type", project.trace_type or "—"),
                ("Source", project.source or "—"),
                ("Traces", str(project.trace_count)),
                ("Created", format_datetime(project.created_at)),
                (
                    "Link",
                    dashboard_link(
                        "project", str(project.id), label="View in Dashboard"
                    ),
                ),
            ]
        )

        content = section(f"Project: {project.name}", info)

        if project.metadata:
            content += f"\n\n### Metadata\n\n```json\n{truncate(str(project.metadata), 500)}\n```"

        # Project versions
        version_data = []
        if params.include_versions:
            versions = ProjectVersion.objects.filter(project=project).order_by(
                "-created_at"
            )[:10]

            if versions:
                content += "\n\n### Versions\n\n"
                rows = []
                for v in versions:
                    rows.append(
                        [
                            f"`{str(v.id)}`",
                            v.version or "—",
                            truncate(v.name, 30),
                            (
                                f"{v.avg_eval_score:.2f}"
                                if v.avg_eval_score is not None
                                else "—"
                            ),
                            format_datetime(v.created_at),
                        ]
                    )
                    version_data.append(
                        {
                            "id": str(v.id),
                            "version": v.version,
                            "name": v.name,
                            "avg_eval_score": (
                                float(v.avg_eval_score)
                                if v.avg_eval_score is not None
                                else None
                            ),
                        }
                    )

                content += markdown_table(
                    ["ID", "Version", "Name", "Avg Score", "Created"], rows
                )
            else:
                content += "\n\n### Versions\n\n_No versions found._"

        data = {
            "id": str(project.id),
            "name": project.name,
            "trace_type": project.trace_type,
            "source": project.source,
            "trace_count": project.trace_count,
            "versions": version_data,
        }

        return ToolResult(content=content, data=data)
