from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import section
from ai_tools.registry import register_tool


class DeleteExperimentInput(PydanticBaseModel):
    experiment_ids: list[UUID] = Field(
        description="List of experiment UUIDs to delete",
        min_length=1,
        max_length=20,
    )


@register_tool
class DeleteExperimentTool(BaseTool):
    name = "delete_experiment"
    description = (
        "Soft-deletes one or more experiments. "
        "Deleted experiments will no longer appear in listings."
    )
    category = "experiments"
    input_model = DeleteExperimentInput

    def execute(
        self, params: DeleteExperimentInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.experiments import ExperimentsTable

        experiments = ExperimentsTable.objects.filter(
            id__in=params.experiment_ids,
            dataset__organization=context.organization,
            deleted=False,
        )
        names = list(experiments.values_list("name", flat=True))
        count = experiments.count()

        if count == 0:
            return ToolResult.error(
                "No matching experiments found.",
                error_code="NOT_FOUND",
            )

        for exp in experiments:
            exp.delete()  # BaseModel.delete() sets deleted + deleted_at

        lines = [f"**Deleted {count} experiment(s):**"]
        for name in names:
            lines.append(f"- {name}")

        return ToolResult(
            content=section("Experiments Deleted", "\n".join(lines)),
            data={"deleted": count, "names": names},
        )
