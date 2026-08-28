from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DeleteRowsInput(PydanticBaseModel):
    dataset_id: str = Field(
        description="Dataset name or UUID. Examples: 'my-qa-dataset' or '550e8400-e29b-41d4-a716-446655440000'"
    )
    row_ids: list[str] = Field(
        description="List of row UUIDs to delete",
        min_length=1,
        max_length=500,
    )


@register_tool
class DeleteRowsTool(BaseTool):
    name = "delete_rows"
    description = (
        "Soft-deletes rows from a dataset. "
        "The rows are marked as deleted but can potentially be recovered. "
        "Use get_dataset_rows to find row IDs."
    )
    category = "datasets"
    input_model = DeleteRowsInput

    def execute(self, params: DeleteRowsInput, context: ToolContext) -> ToolResult:

        from ai_tools.resolvers import resolve_dataset
        from model_hub.models.develop_dataset import Row
        from model_hub.services.dataset_service import ServiceError
        from model_hub.services.dataset_service import delete_rows as svc_delete_rows

        ds, error = resolve_dataset(
            params.dataset_id, context.organization, context.workspace
        )
        if error:
            return ToolResult.error(error, error_code="NOT_FOUND")

        result = svc_delete_rows(
            dataset_id=str(ds.id),
            row_ids=[str(r) for r in params.row_ids],
            organization=context.organization,
        )

        if isinstance(result, ServiceError):
            return ToolResult.error(result.message, error_code=result.code)

        remaining = Row.objects.filter(
            dataset_id=result["dataset_id"], deleted=False
        ).count()

        info = key_value_block(
            [
                ("Dataset ID", f"`{result['dataset_id']}`"),
                ("Rows Deleted", str(result["deleted"])),
                ("Remaining Rows", str(remaining)),
                (
                    "Link",
                    dashboard_link(
                        "dataset", result["dataset_id"], label="View in Dashboard"
                    ),
                ),
            ]
        )

        return ToolResult(
            content=section("Rows Deleted", info),
            data={"deleted": result["deleted"], "remaining": remaining},
        )
