import json

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class UpdateCellValueInput(PydanticBaseModel):
    dataset_id: str = Field(
        description="Dataset name or UUID. Examples: 'my-qa-dataset' or '550e8400-e29b-41d4-a716-446655440000'"
    )
    updates: dict[str, str] = Field(
        description=(
            "Map of cell_id (UUID string) to new value. "
            "Example: {'cell-uuid-1': 'new value', 'cell-uuid-2': 'another value'}"
        ),
        min_length=1,
    )


@register_tool
class UpdateCellValueTool(BaseTool):
    name = "update_cell_value"
    description = (
        "Updates individual cell values in a dataset. "
        "Provide a mapping of cell IDs to their new values. "
        "Use get_dataset_rows to find cell IDs first."
    )
    category = "datasets"
    input_model = UpdateCellValueInput

    def execute(self, params: UpdateCellValueInput, context: ToolContext) -> ToolResult:

        from ai_tools.resolvers import resolve_dataset
        from model_hub.models.choices import CellStatus
        from model_hub.models.develop_dataset import Cell
        from model_hub.services.dataset_validators import (
            MAX_CELL_VALUE_LENGTH,
            validate_and_convert_cell_value,
            validate_column_is_editable,
        )

        dataset, error = resolve_dataset(
            params.dataset_id, context.organization, context.workspace
        )
        if error:
            return ToolResult.error(error, error_code="NOT_FOUND")

        # Pre-fetch columns for type validation (avoids N+1)
        cell_ids = list(params.updates.keys())
        cells = Cell.objects.filter(
            id__in=cell_ids, dataset=dataset, deleted=False
        ).select_related("column")
        cell_map = {str(c.id): c for c in cells}

        updated = 0
        errors = []
        for cell_id, new_value in params.updates.items():
            cell = cell_map.get(cell_id)
            if not cell:
                errors.append(f"Cell `{cell_id}` not found")
                continue

            # Check if column is editable
            is_editable, edit_err = validate_column_is_editable(cell.column)
            if not is_editable:
                errors.append(f"Cell `{cell_id}`: {edit_err}")
                continue

            # Check max value length
            if isinstance(new_value, str) and len(new_value) > MAX_CELL_VALUE_LENGTH:
                errors.append(
                    f"Cell `{cell_id}`: Value exceeds maximum length of "
                    f"{MAX_CELL_VALUE_LENGTH} characters"
                )
                continue

            data_type = cell.column.data_type if cell.column else "text"
            converted, error = validate_and_convert_cell_value(new_value, data_type)
            if error:
                errors.append(f"Cell `{cell_id}`: {error}")
                continue

            cell.value = converted
            cell.status = CellStatus.PASS.value
            cell.value_infos = json.dumps({})
            cell.save(update_fields=["value", "status", "value_infos", "updated_at"])
            updated += 1

        info = key_value_block(
            [
                ("Dataset", dataset.name),
                ("Cells Updated", str(updated)),
                ("Errors", str(len(errors)) if errors else "None"),
                (
                    "Link",
                    dashboard_link(
                        "dataset", str(dataset.id), label="View in Dashboard"
                    ),
                ),
            ]
        )

        content = section("Cells Updated", info)
        if errors:
            content += "\n\n### Errors\n\n" + "\n".join(f"- {e}" for e in errors)

        return ToolResult(
            content=content,
            data={"updated": updated, "errors": errors},
            is_error=len(errors) > 0 and updated == 0,
        )
