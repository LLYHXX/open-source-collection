from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    format_status,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListEvalTasksInput(PydanticBaseModel):
    project_id: UUID = Field(
        description="The UUID of the project to list eval tasks for"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: pending, running, completed, failed, paused",
    )
    name: Optional[str] = Field(
        default=None,
        description="Filter by name (case-insensitive contains match)",
    )


@register_tool
class ListEvalTasksTool(BaseTool):
    name = "list_eval_tasks"
    description = (
        "Lists eval tasks for a tracing project. Eval tasks are batch jobs that "
        "run evaluations on spans. Use this to see the status of evaluation runs "
        "on a project."
    )
    category = "tracing"
    input_model = ListEvalTasksInput

    def execute(self, params: ListEvalTasksInput, context: ToolContext) -> ToolResult:

        from tracer.models.eval_task import EvalTask
        from tracer.models.project import Project

        try:
            project = Project.objects.get(
                id=params.project_id, organization=context.organization
            )
        except Project.DoesNotExist:
            return ToolResult.not_found("Project", str(params.project_id))

        qs = (
            EvalTask.objects.filter(project=project, deleted=False)
            .select_related("project")
            .prefetch_related("evals")
            .order_by("-created_at")
        )

        if params.status:
            qs = qs.filter(status=params.status)

        if params.name:
            qs = qs.filter(name__icontains=params.name)

        total = qs.count()
        tasks = qs[params.offset : params.offset + params.limit]

        if not tasks:
            return ToolResult(
                content=section(
                    f"Eval Tasks: {project.name}",
                    "_No eval tasks found. Use `create_eval_task` to create one._",
                ),
                data={"tasks": [], "total": 0, "project_id": str(project.id)},
            )

        rows = []
        data_list = []
        for task in tasks:
            eval_names = [e.name for e in task.evals.filter(deleted=False)]
            evals_str = truncate(", ".join(eval_names), 40) if eval_names else "—"

            rows.append(
                [
                    f"`{task.id}`",
                    task.name or "—",
                    format_status(task.status),
                    task.run_type or "—",
                    f"{task.sampling_rate}%",
                    evals_str,
                    format_datetime(task.last_run),
                    format_datetime(task.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(task.id),
                    "name": task.name,
                    "status": task.status,
                    "run_type": task.run_type,
                    "sampling_rate": task.sampling_rate,
                    "evals": eval_names,
                    "last_run": str(task.last_run) if task.last_run else None,
                    "created_at": str(task.created_at) if task.created_at else None,
                }
            )

        table = markdown_table(
            [
                "ID",
                "Name",
                "Status",
                "Run Type",
                "Sampling %",
                "Evals",
                "Last Run",
                "Created",
            ],
            rows,
        )

        content = section(
            f"Eval Tasks: {project.name} ({total})",
            f"Showing {len(rows)} of {total}\n\n{table}",
        )

        return ToolResult(
            content=content,
            data={"tasks": data_list, "total": total, "project_id": str(project.id)},
        )
