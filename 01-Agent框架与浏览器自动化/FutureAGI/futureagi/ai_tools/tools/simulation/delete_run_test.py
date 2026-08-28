from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DeleteRunTestInput(PydanticBaseModel):
    run_test_id: UUID = Field(description="The UUID of the run test to delete")


@register_tool
class DeleteRunTestTool(BaseTool):
    name = "delete_run_test"
    description = "Soft-deletes a test suite (RunTest) by marking it as deleted."
    category = "simulation"
    input_model = DeleteRunTestInput

    def execute(self, params: DeleteRunTestInput, context: ToolContext) -> ToolResult:
        from django.utils import timezone

        from simulate.models.run_test import RunTest

        try:
            run_test = RunTest.objects.get(
                id=params.run_test_id, organization=context.organization
            )
        except RunTest.DoesNotExist:
            return ToolResult.not_found("Run Test", str(params.run_test_id))

        run_test_name = run_test.name
        run_test.deleted = True
        run_test.deleted_at = timezone.now()
        run_test.save(update_fields=["deleted", "deleted_at", "updated_at"])

        info = key_value_block(
            [
                ("ID", f"`{params.run_test_id}`"),
                ("Name", run_test_name),
                ("Status", "Deleted"),
            ]
        )

        content = section("Test Suite Deleted", info)

        return ToolResult(
            content=content,
            data={
                "id": str(params.run_test_id),
                "name": run_test_name,
                "deleted": True,
            },
        )
