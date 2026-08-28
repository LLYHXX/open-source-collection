from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DeleteColumnInput(PydanticBaseModel):
    dataset_id: str = Field(
        description="Dataset name or UUID. Examples: 'my-qa-dataset' or '550e8400-e29b-41d4-a716-446655440000'"
    )
    column_id: str = Field(description="The UUID of the column to delete")


@register_tool
class DeleteColumnTool(BaseTool):
    name = "delete_column"
    description = (
        "Deletes a column and all its cell values from a dataset. "
        "This is a soft delete — the column is marked as deleted."
    )
    category = "datasets"
    input_model = DeleteColumnInput

    def execute(self, params: DeleteColumnInput, context: ToolContext) -> ToolResult:

        from ai_tools.resolvers import resolve_dataset
        from model_hub.services.dataset_service import (
            ServiceError,
        )
        from model_hub.services.dataset_service import (
            delete_column as svc_delete_column,
        )

        ds, error = resolve_dataset(
            params.dataset_id, context.organization, context.workspace
        )
        if error:
            return ToolResult.error(error, error_code="NOT_FOUND")

        result = svc_delete_column(
            dataset_id=str(ds.id),
            column_id=str(params.column_id),
            organization=context.organization,
        )

        if isinstance(result, ServiceError):
            return ToolResult.error(result.message, error_code=result.code)

        info = key_value_block(
            [
                ("Dataset ID", f"`{result['dataset_id']}`"),
                ("Column Deleted", result["column_name"]),
                (
                    "Link",
                    dashboard_link(
                        "dataset", result["dataset_id"], label="View in Dashboard"
                    ),
                ),
            ]
        )

        return ToolResult(
            content=section("Column Deleted", info),
            data={
                "column_name": result["column_name"],
                "column_id": result["column_id"],
            },
        )
