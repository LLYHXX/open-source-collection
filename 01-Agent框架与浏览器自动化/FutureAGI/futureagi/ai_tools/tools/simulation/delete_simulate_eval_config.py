from uuid import UUID

from django.utils import timezone
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DeleteSimulateEvalConfigInput(PydanticBaseModel):
    run_test_id: UUID = Field(
        description="The UUID of the RunTest that owns the eval config"
    )
    eval_config_id: UUID = Field(
        description="The UUID of the SimulateEvalConfig to delete"
    )


@register_tool
class DeleteSimulateEvalConfigTool(BaseTool):
    name = "delete_simulate_eval_config"
    description = (
        "Deletes an evaluation config from a simulation run test. "
        "Cannot delete the last eval config — at least one must remain."
    )
    category = "simulation"
    input_model = DeleteSimulateEvalConfigInput

    def execute(
        self, params: DeleteSimulateEvalConfigInput, context: ToolContext
    ) -> ToolResult:
        from simulate.models.eval_config import SimulateEvalConfig
        from simulate.models.run_test import RunTest

        # Get the run test
        try:
            run_test = RunTest.objects.get(
                id=params.run_test_id,
                organization=context.organization,
                deleted=False,
            )
        except RunTest.DoesNotExist:
            return ToolResult.not_found("Run Test", str(params.run_test_id))

        # Get the eval config
        try:
            eval_config = SimulateEvalConfig.objects.get(
                id=params.eval_config_id,
                run_test=run_test,
                deleted=False,
            )
        except SimulateEvalConfig.DoesNotExist:
            return ToolResult.not_found("Eval Config", str(params.eval_config_id))

        # Ensure at least one eval config remains
        active_count = SimulateEvalConfig.objects.filter(
            run_test=run_test, deleted=False
        ).count()
        if active_count <= 1:
            return ToolResult.error(
                "Cannot delete the last evaluation config. "
                "At least one evaluation config must remain.",
                error_code="VALIDATION_ERROR",
            )

        eval_name = eval_config.name
        eval_config.deleted = True
        eval_config.deleted_at = timezone.now()
        eval_config.save(update_fields=["deleted", "deleted_at"])

        info = key_value_block(
            [
                ("Eval Config", eval_name),
                ("ID", f"`{params.eval_config_id}`"),
                ("Test", run_test.name),
                ("Status", "Deleted"),
            ]
        )

        content = section("Evaluation Config Deleted", info)

        return ToolResult(
            content=content,
            data={
                "eval_config_id": str(params.eval_config_id),
                "eval_config_name": eval_name,
                "run_test_id": str(params.run_test_id),
                "deleted": True,
                "deleted_at": timezone.now(),
            },
        )
