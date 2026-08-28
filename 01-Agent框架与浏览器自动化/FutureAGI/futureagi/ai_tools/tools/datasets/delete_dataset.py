from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import section
from ai_tools.registry import register_tool
from model_hub.constants import MAX_BATCH_DELETE_SIZE


class DeleteDatasetInput(PydanticBaseModel):
    dataset_ids: list[str] = Field(
        description="List of dataset names or UUIDs to delete",
        min_length=1,
        max_length=MAX_BATCH_DELETE_SIZE,
    )


@register_tool
class DeleteDatasetTool(BaseTool):
    name = "delete_dataset"
    description = (
        "Soft-deletes one or more datasets. "
        "This marks datasets as deleted; they will no longer appear in listings."
    )
    category = "datasets"
    input_model = DeleteDatasetInput

    def execute(self, params: DeleteDatasetInput, context: ToolContext) -> ToolResult:

        from ai_tools.resolvers import resolve_dataset
        from model_hub.services.dataset_service import ServiceError
        from model_hub.services.dataset_service import delete_datasets as svc_delete

        # Resolve each identifier to a dataset UUID
        resolved_ids = []
        for identifier in params.dataset_ids:
            ds, error = resolve_dataset(
                identifier, context.organization, context.workspace
            )
            if error:
                return ToolResult.error(error, error_code="NOT_FOUND")
            resolved_ids.append(str(ds.id))

        result = svc_delete(
            dataset_ids=resolved_ids,
            organization=context.organization,
        )

        if isinstance(result, ServiceError):
            return ToolResult.error(result.message, error_code=result.code)

        lines = [f"**Deleted {result['deleted']} dataset(s):**"]
        for name in result["names"]:
            lines.append(f"- {name}")

        return ToolResult(
            content=section("Datasets Deleted", "\n".join(lines)),
            data={"deleted": result["deleted"], "names": result["names"]},
        )
