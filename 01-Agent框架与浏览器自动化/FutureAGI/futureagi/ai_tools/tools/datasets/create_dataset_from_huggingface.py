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
from model_hub.constants import MAX_DATASET_NAME_LENGTH


class CreateDatasetFromHuggingFaceInput(PydanticBaseModel):
    huggingface_dataset_name: str = Field(
        description=(
            "HuggingFace dataset identifier "
            "(e.g. 'squad', 'glue', 'imdb', 'tatsu-lab/alpaca')"
        ),
        min_length=1,
    )
    huggingface_dataset_config: Optional[str] = Field(
        default=None,
        description=(
            "Dataset configuration/subset name. "
            "Required for multi-config datasets (e.g. 'mrpc' for glue)."
        ),
    )
    huggingface_dataset_split: str = Field(
        description="Dataset split to import (e.g. 'train', 'test', 'validation')",
        min_length=1,
    )
    name: Optional[str] = Field(
        default=None,
        max_length=MAX_DATASET_NAME_LENGTH,
        description=(
            "Name for the new dataset. Defaults to the HuggingFace dataset name "
            "with '/' replaced by '_'."
        ),
    )
    num_rows: Optional[int] = Field(
        default=None,
        ge=1,
        description=(
            "Maximum number of rows to import. "
            "If omitted, imports all rows from the split."
        ),
    )
    model_type: Optional[str] = Field(
        default=None,
        description="Model type for the dataset (e.g. 'GenerativeLLM')",
    )


@register_tool
class CreateDatasetFromHuggingFaceTool(BaseTool):
    name = "create_dataset_from_huggingface"
    description = (
        "Creates a dataset by importing data from a HuggingFace dataset. "
        "Fetches the dataset schema, creates columns automatically, and "
        "processes rows in the background. "
        "Requires the HuggingFace dataset path and split name."
    )
    category = "datasets"
    input_model = CreateDatasetFromHuggingFaceInput

    def execute(
        self, params: CreateDatasetFromHuggingFaceInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.services.dataset_service import (
            ServiceError,
            create_dataset_from_huggingface,
        )

        result = create_dataset_from_huggingface(
            hf_dataset_name=params.huggingface_dataset_name,
            hf_config=params.huggingface_dataset_config,
            hf_split=params.huggingface_dataset_split,
            name=params.name,
            organization=context.organization,
            workspace=context.workspace,
            user=context.user,
            model_type=params.model_type,
            num_rows=params.num_rows,
        )

        if isinstance(result, ServiceError):
            return ToolResult.error(result.message, error_code=result.code)

        info = key_value_block(
            [
                ("Dataset ID", f"`{result['dataset_id']}`"),
                ("Name", result["name"]),
                ("Rows", str(result["rows"])),
                ("Columns", str(result["columns"])),
                (
                    "Column Names",
                    ", ".join(f"`{n}`" for n in result["column_names"]),
                ),
                ("Status", result["processing_status"]),
                (
                    "Link",
                    dashboard_link(
                        "dataset", result["dataset_id"], label="View in Dashboard"
                    ),
                ),
            ]
        )

        content = section("Dataset Created from HuggingFace", info)
        content += (
            "\n\n_Data is being processed in the background. "
            "Rows will be populated shortly._"
        )

        return ToolResult(content=content, data=result)
