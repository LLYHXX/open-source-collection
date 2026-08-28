import base64
from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool
from model_hub.constants import (
    MAX_DATASET_NAME_LENGTH,
    MAX_FILE_SIZE_BYTES,
)


class CreateDatasetFromFileInput(PydanticBaseModel):
    name: str = Field(
        description="Name for the new dataset",
        min_length=1,
        max_length=MAX_DATASET_NAME_LENGTH,
    )
    file_content_base64: str = Field(
        description=(
            "Base64-encoded file content. Supported formats: "
            "CSV (.csv), JSON (.json), JSONL (.jsonl), Excel (.xls, .xlsx)."
        ),
    )
    file_name: str = Field(
        description=(
            "Original file name with extension (e.g. 'data.csv', 'records.jsonl'). "
            "Used to detect file format."
        ),
        min_length=1,
    )
    model_type: Optional[str] = Field(
        default=None,
        description="Model type for the dataset (e.g. 'GenerativeLLM')",
    )


@register_tool
class CreateDatasetFromFileTool(BaseTool):
    name = "create_dataset_from_file"
    description = (
        "Creates a dataset by uploading file content (CSV, JSON, JSONL, Excel). "
        "The file is validated, parsed, and processed in the background. "
        "Returns the dataset ID and estimated row/column counts."
    )
    category = "datasets"
    input_model = CreateDatasetFromFileInput

    def execute(
        self, params: CreateDatasetFromFileInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.services.dataset_service import (
            ServiceError,
            create_dataset_from_file,
        )

        # Decode base64 content
        try:
            file_content = base64.b64decode(params.file_content_base64)
        except Exception:
            return ToolResult.error(
                "Invalid base64-encoded file content.",
                error_code="VALIDATION_ERROR",
            )

        # Validate decoded size
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            return ToolResult.error(
                f"File size ({len(file_content)} bytes) exceeds the maximum "
                f"allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
                error_code="VALIDATION_ERROR",
            )

        result = create_dataset_from_file(
            file_content=file_content,
            file_name=params.file_name,
            name=params.name,
            organization=context.organization,
            workspace=context.workspace,
            user=context.user,
            model_type=params.model_type,
        )

        if isinstance(result, ServiceError):
            return ToolResult.error(result.message, error_code=result.code)

        info = key_value_block(
            [
                ("Dataset ID", f"`{result['dataset_id']}`"),
                ("Name", result["name"]),
                ("Estimated Rows", str(result["estimated_rows"])),
                ("Estimated Columns", str(result["estimated_columns"])),
                ("Status", result["processing_status"]),
                (
                    "Link",
                    dashboard_link(
                        "dataset", result["dataset_id"], label="View in Dashboard"
                    ),
                ),
            ]
        )

        content = section("Dataset Created from File", info)
        content += (
            "\n\n_File is being processed in the background. "
            "Rows will appear shortly._"
        )

        return ToolResult(content=content, data=result)
