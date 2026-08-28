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


class ListPromptSimulationsInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template")
    version_id: Optional[UUID] = Field(
        default=None, description="Filter by specific version UUID"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


@register_tool
class ListPromptSimulationsTool(BaseTool):
    name = "list_prompt_simulations"
    description = (
        "Lists prompt simulation runs for a specific template. "
        "Shows simulation name, version, scenario count, and last execution status."
    )
    category = "prompts"
    input_model = ListPromptSimulationsInput

    def execute(
        self, params: ListPromptSimulationsInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.run_prompt import PromptTemplate
        from simulate.models import RunTest
        from simulate.models.test_execution import TestExecution

        try:
            template = PromptTemplate.objects.get(
                id=params.template_id,
                organization=context.organization,
                deleted=False,
            )
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        qs = (
            RunTest.objects.filter(
                prompt_template=template,
                source_type="prompt",
                organization=context.organization,
                deleted=False,
            )
            .prefetch_related("scenarios")
            .order_by("-created_at")
        )

        if params.version_id:
            qs = qs.filter(prompt_version_id=params.version_id)

        total = qs.count()
        simulations = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for sim in simulations:
            # Get latest execution status
            latest_exec = (
                TestExecution.objects.filter(run_test=sim, deleted=False)
                .order_by("-created_at")
                .first()
            )

            exec_status = format_status(latest_exec.status) if latest_exec else "—"
            version_label = (
                sim.prompt_version.template_version if sim.prompt_version else "—"
            )
            scenario_count = sim.scenarios.filter(deleted=False).count()

            rows.append(
                [
                    f"`{sim.id}`",
                    truncate(sim.name, 35),
                    version_label,
                    str(scenario_count),
                    exec_status,
                    format_datetime(sim.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(sim.id),
                    "name": sim.name,
                    "version": version_label,
                    "version_id": (
                        str(sim.prompt_version_id) if sim.prompt_version_id else None
                    ),
                    "scenario_count": scenario_count,
                    "last_status": latest_exec.status if latest_exec else None,
                }
            )

        table = markdown_table(
            ["ID", "Name", "Version", "Scenarios", "Last Status", "Created"],
            rows,
        )

        showing = f"Showing {len(rows)} of {total}"
        content = section(
            f"Prompt Simulations: {template.name} ({total})",
            f"{showing}\n\n{table}",
        )

        if total > params.offset + params.limit:
            content += f"\n\n_Use offset={params.offset + params.limit} to see more._"

        return ToolResult(
            content=content, data={"simulations": data_list, "total": total}
        )
