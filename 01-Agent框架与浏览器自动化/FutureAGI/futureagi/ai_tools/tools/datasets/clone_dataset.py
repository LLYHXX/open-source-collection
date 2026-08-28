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


class CloneDatasetInput(PydanticBaseModel):
    dataset_id: str = Field(
        description="Dataset name or UUID. Examples: 'my-qa-dataset' or '550e8400-e29b-41d4-a716-446655440000'"
    )
    new_name: Optional[str] = Field(
        default=None,
        max_length=MAX_DATASET_NAME_LENGTH,
        description="Name for the cloned dataset. Defaults to 'Copy of <original>'.",
    )


@register_tool
class CloneDatasetTool(BaseTool):
    name = "clone_dataset"
    description = (
        "Creates a full copy of a dataset including all columns, rows, and cell values. "
        "The new dataset is independent of the original."
    )
    category = "datasets"
    input_model = CloneDatasetInput

    def execute(self, params: CloneDatasetInput, context: ToolContext) -> ToolResult:

        from ai_tools.resolvers import resolve_dataset
        from model_hub.services.dataset_service import ServiceError
        from model_hub.services.dataset_service import clone_dataset as svc_clone

        ds, error = resolve_dataset(
            params.dataset_id, context.organization, context.workspace
        )
        if error:
            return ToolResult.error(error, error_code="NOT_FOUND")

        result = svc_clone(
            source_dataset_id=str(ds.id),
            new_name=params.new_name,
            organization=context.organization,
            workspace=context.workspace,
            user=context.user,
        )

        if isinstance(result, ServiceError):
            if "already exists" in result.message.lower():
                from model_hub.models.develop_dataset import Dataset

                existing = Dataset.objects.filter(
                    name__icontains=params.new_name or "",
                    organization=context.organization,
                ).first()
                if existing:
                    return ToolResult.error(
                        f"{result.message} Existing dataset ID: `{existing.id}`. "
                        f"Use this ID or choose a different name.",
                        error_code=result.code,
                    )
            return ToolResult.error(result.message, error_code=result.code)

        info = key_value_block(
            [
                ("New Dataset ID", f"`{result['dataset_id']}`"),
                ("Name", result["name"]),
                ("Source", f"Cloned from `{result['source_dataset_id']}`"),
                ("Columns", str(result["columns_cloned"])),
                ("Rows", str(result["rows_cloned"])),
                (
                    "Link",
                    dashboard_link(
                        "dataset", result["dataset_id"], label="View in Dashboard"
                    ),
                ),
            ]
        )

        return ToolResult(
            content=section("Dataset Cloned", info),
            data={
                "dataset_id": result["dataset_id"],
                "name": result["name"],
                "rows": result["rows_cloned"],
                "columns": result["columns_cloned"],
            },
        )
