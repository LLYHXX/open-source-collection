from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    key_value_block,
    markdown_table,
    section,
)
from ai_tools.registry import register_tool

DataTypeLiteral = Literal[
    "text",
    "boolean",
    "integer",
    "float",
    "json",
    "array",
    "image",
    "images",
    "datetime",
    "audio",
    "document",
]


class ColumnDef(PydanticBaseModel):
    name: str = Field(description="Column name", min_length=1, max_length=255)
    data_type: DataTypeLiteral = Field(
        default="text",
        description=(
            "Data type: text, integer, float, boolean, json, "
            "array, image, images, datetime, audio, document"
        ),
    )


class AddColumnsInput(PydanticBaseModel):
    dataset_id: str = Field(
        description="Dataset name or UUID. Examples: 'my-qa-dataset' or '550e8400-e29b-41d4-a716-446655440000'"
    )
    columns: list[ColumnDef] = Field(
        description="List of columns to add with name and data_type",
        min_length=1,
        max_length=20,
    )


@register_tool
class AddColumnsTool(BaseTool):
    name = "add_columns"
    description = (
        "Adds new columns to an existing dataset. "
        "Existing rows will have empty cells for the new columns."
    )
    category = "datasets"
    input_model = AddColumnsInput

    def execute(self, params: AddColumnsInput, context: ToolContext) -> ToolResult:

        from ai_tools.resolvers import resolve_dataset
        from model_hub.services.dataset_service import ServiceError
        from model_hub.services.dataset_service import add_columns as svc_add_columns

        # data_type is already validated by the Literal type in ColumnDef.

        ds, error = resolve_dataset(
            params.dataset_id, context.organization, context.workspace
        )
        if error:
            return ToolResult.error(error, error_code="NOT_FOUND")

        columns_data = [
            {"name": c.name, "data_type": c.data_type} for c in params.columns
        ]

        result = svc_add_columns(
            dataset_id=str(ds.id),
            columns_data=columns_data,
            organization=context.organization,
        )

        if isinstance(result, ServiceError):
            return ToolResult.error(result.message, error_code=result.code)

        rows_table = [
            [c["name"], c["data_type"], f"`{c['id']}`"] for c in result["columns"]
        ]
        table = markdown_table(["Name", "Type", "ID"], rows_table)

        info = key_value_block(
            [
                ("Dataset ID", f"`{result['dataset_id']}`"),
                ("Columns Added", str(result["columns_added"])),
                (
                    "Link",
                    dashboard_link(
                        "dataset", result["dataset_id"], label="View in Dashboard"
                    ),
                ),
            ]
        )

        content = section("Columns Added", info)
        content += f"\n\n### New Columns\n\n{table}"

        return ToolResult(
            content=content,
            data={"columns": result["columns"]},
        )
