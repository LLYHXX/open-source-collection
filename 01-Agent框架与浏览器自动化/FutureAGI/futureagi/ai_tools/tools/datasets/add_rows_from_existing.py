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


class AddRowsFromExistingInput(PydanticBaseModel):
    target_dataset_id: UUID = Field(
        description="The UUID of the dataset to add rows TO"
    )
    source_dataset_id: UUID = Field(
        description="The UUID of the dataset to copy rows FROM"
    )
    column_mapping: dict[str, str] = Field(
        description=(
            "Map of source column names to target column names. "
            "Example: {'source_input': 'target_input', 'source_output': 'target_output'}"
        ),
        min_length=1,
    )


@register_tool
class AddRowsFromExistingTool(BaseTool):
    name = "add_rows_from_existing"
    description = (
        "Copies rows from one dataset to another using a column name mapping. "
        "Use list_datasets and get_dataset_rows to find dataset IDs and column names."
    )
    category = "datasets"
    input_model = AddRowsFromExistingInput

    def execute(
        self, params: AddRowsFromExistingInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.services.dataset_service import (
            ServiceError,
        )
        from model_hub.services.dataset_service import (
            add_rows_from_existing as svc_add_from_existing,
        )

        result = svc_add_from_existing(
            target_dataset_id=str(params.target_dataset_id),
            source_dataset_id=str(params.source_dataset_id),
            column_mapping=params.column_mapping,
            organization=context.organization,
            workspace=context.workspace,
        )

        if isinstance(result, ServiceError):
            return ToolResult.error(result.message, error_code=result.code)

        info = key_value_block(
            [
                ("Target Dataset", result["target_dataset_name"]),
                ("Source Dataset ID", f"`{result['source_dataset_id']}`"),
                ("Rows Added", str(result["rows_added"])),
                ("Columns Mapped", str(result["columns_mapped"])),
                (
                    "Link",
                    dashboard_link(
                        "dataset",
                        result["target_dataset_id"],
                        label="View Target in Dashboard",
                    ),
                ),
            ]
        )

        return ToolResult(
            content=section("Rows Added from Existing Dataset", info),
            data={
                "target_dataset_id": result["target_dataset_id"],
                "rows_added": result["rows_added"],
                "columns_mapped": result["columns_mapped"],
            },
        )
