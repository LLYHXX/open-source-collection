from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DuplicateDatasetInput(PydanticBaseModel):
    dataset_id: UUID = Field(description="The UUID of the dataset to duplicate")
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Name for the duplicated dataset",
    )
    row_ids: Optional[list[UUID]] = Field(
        default=None,
        description=(
            "Optional list of specific row UUIDs to include. "
            "If omitted, all rows are duplicated."
        ),
    )


@register_tool
class DuplicateDatasetTool(BaseTool):
    name = "duplicate_dataset"
    description = (
        "Creates a new dataset by duplicating an existing one. "
        "Optionally specify which rows to include. "
        "Copies columns and cell values to the new dataset."
    )
    category = "datasets"
    input_model = DuplicateDatasetInput

    def execute(
        self, params: DuplicateDatasetInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.services.dataset_service import (
            ServiceError,
        )
        from model_hub.services.dataset_service import (
            duplicate_dataset as svc_duplicate,
        )

        result = svc_duplicate(
            dataset_id=str(params.dataset_id),
            name=params.name,
            row_ids=[str(r) for r in params.row_ids] if params.row_ids else None,
            organization=context.organization,
            workspace=context.workspace,
            user=context.user,
        )

        if isinstance(result, ServiceError):
            return ToolResult.error(result.message, error_code=result.code)

        info = key_value_block(
            [
                ("New Dataset ID", f"`{result['dataset_id']}`"),
                ("Name", result["dataset_name"]),
                ("Source", f"Duplicated from `{result['source_dataset_id']}`"),
                ("Rows Copied", str(result["rows_copied"])),
                ("Columns Copied", str(result["columns_copied"])),
                (
                    "Link",
                    dashboard_link(
                        "dataset", result["dataset_id"], label="View in Dashboard"
                    ),
                ),
            ]
        )

        return ToolResult(
            content=section("Dataset Duplicated", info),
            data={
                "dataset_id": result["dataset_id"],
                "name": result["dataset_name"],
                "rows_copied": result["rows_copied"],
                "columns_copied": result["columns_copied"],
            },
        )
