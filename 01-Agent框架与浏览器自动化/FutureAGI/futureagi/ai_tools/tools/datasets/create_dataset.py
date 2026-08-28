from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool
from model_hub.constants import (
    MAX_DATASET_NAME_LENGTH,
    MAX_MANUAL_COLUMNS,
    MAX_MANUAL_ROWS,
)


class CreateDatasetInput(PydanticBaseModel):
    name: str = Field(
        description="Name for the new dataset",
        min_length=1,
        max_length=MAX_DATASET_NAME_LENGTH,
    )
    columns: list[str] = Field(
        description="List of column names to create (e.g. ['input', 'expected_output', 'context'])",
        min_length=1,
        max_length=MAX_MANUAL_COLUMNS,
    )
    column_types: Optional[list[str]] = Field(
        default=None,
        description=(
            "Data type for each column: text, integer, float, boolean, json, "
            "array, image, images, datetime, audio, document. "
            "Must match length of columns. Defaults to 'text' for all."
        ),
    )
    number_of_rows: Optional[int] = Field(
        default=None,
        ge=0,
        le=MAX_MANUAL_ROWS,
        description=(
            "Number of empty rows to create (0-100). "
            "If omitted or 0, the dataset is created with columns only."
        ),
    )

    @field_validator("columns", mode="before")
    @classmethod
    def normalize_columns(cls, v):
        """Handle LLMs sending columns as dicts or stringified JSON."""
        import json as _json

        # Handle stringified JSON
        if isinstance(v, str):
            try:
                v = _json.loads(v)
            except (ValueError, TypeError):
                return [v]

        if not isinstance(v, list):
            return v

        # Handle list of dicts like [{"name": "col1", "type": "text"}]
        normalized = []
        for item in v:
            if isinstance(item, dict):
                normalized.append(item.get("name", item.get("column_name", str(item))))
            else:
                normalized.append(str(item))
        return normalized


VALID_DATA_TYPES = {
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
    "others",
    "persona",
}


@register_tool
class CreateDatasetTool(BaseTool):
    name = "create_dataset"
    description = (
        "Creates a new empty dataset with the specified columns. "
        "Returns the dataset ID for adding rows or running evaluations."
    )
    category = "datasets"
    input_model = CreateDatasetInput

    def execute(self, params: CreateDatasetInput, context: ToolContext) -> ToolResult:

        from model_hub.services.dataset_service import ServiceError, create_dataset

        # Validate column types if provided
        if params.column_types:
            if len(params.column_types) != len(params.columns):
                return ToolResult.error(
                    f"column_types length ({len(params.column_types)}) must match "
                    f"columns length ({len(params.columns)}).",
                    error_code="VALIDATION_ERROR",
                )
            for ct in params.column_types:
                if ct not in VALID_DATA_TYPES:
                    return ToolResult.error(
                        f"Invalid column type '{ct}'. Valid types: {', '.join(sorted(VALID_DATA_TYPES))}",
                        error_code="VALIDATION_ERROR",
                    )

        types = params.column_types or ["text"] * len(params.columns)

        # Build column defs for service
        columns_def = [
            {"name": name, "data_type": dtype}
            for name, dtype in zip(params.columns, types)
        ]

        result = create_dataset(
            name=params.name,
            columns=columns_def,
            organization=context.organization,
            workspace=context.workspace,
            user=context.user,
        )

        if isinstance(result, ServiceError):
            # If name collision, include the existing dataset's ID so the agent can use it
            if "already exists" in result.message.lower():
                from model_hub.models.develop_dataset import Dataset

                existing = Dataset.objects.filter(
                    name=params.name,
                    organization=context.organization,
                ).first()
                if existing:
                    return ToolResult.error(
                        f"{result.message} Existing dataset ID: `{existing.id}`. "
                        f"Use this ID to work with the existing dataset, or choose a different name.",
                        error_code=result.code,
                    )
            return ToolResult.error(result.message, error_code=result.code)

        # Create empty rows if requested (aligned with ManuallyCreateDatasetView)
        rows_created = 0
        if params.number_of_rows and params.number_of_rows > 0:
            from model_hub.services.dataset_service import add_dataset_rows

            empty_rows = [{} for _ in range(params.number_of_rows)]
            row_result = add_dataset_rows(
                dataset_id=result["dataset_id"],
                rows=empty_rows,
                organization=context.organization,
                workspace=context.workspace,
            )
            if isinstance(row_result, ServiceError):
                return ToolResult.error(row_result.message, error_code=row_result.code)
            rows_created = row_result["rows_added"]

        info = key_value_block(
            [
                ("Dataset ID", f"`{result['dataset_id']}`"),
                ("Name", result["name"]),
                ("Columns", str(len(result["columns"]))),
                (
                    "Column Details",
                    ", ".join(
                        f"`{c['name']}` ({c['data_type']})" for c in result["columns"]
                    ),
                ),
                (
                    "Link",
                    dashboard_link(
                        "dataset", result["dataset_id"], label="View in Dashboard"
                    ),
                ),
            ]
        )

        content = section("Dataset Created", info)
        if rows_created:
            content += f"\n\n_Created {rows_created} empty row(s)._"
        else:
            content += "\n\n_Dataset is empty. Add rows via the dashboard or API._"

        return ToolResult(
            content=content,
            data={
                "dataset_id": result["dataset_id"],
                "name": result["name"],
                "columns": [
                    {"id": c["id"], "name": c["name"], "type": c["data_type"]}
                    for c in result["columns"]
                ],
                "rows_created": rows_created,
            },
        )
