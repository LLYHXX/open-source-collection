import json
from typing import List

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class EvalTagItem(PydanticBaseModel):
    custom_eval_name: str = Field(description="Name of the custom eval config")
    eval_name: str = Field(description="Name of the eval template")
    mapping: dict = Field(
        default_factory=dict,
        description="Mapping of template keys to span attributes",
    )


class CheckEvalConfigExistsInput(PydanticBaseModel):
    project_name: str = Field(
        description="Name of the project to check",
        min_length=1,
    )
    eval_tags: List[EvalTagItem] = Field(
        description=(
            "List of eval tag configurations to check for conflicts. "
            "Each has custom_eval_name, eval_name, and mapping."
        ),
        min_length=1,
    )
    project_type: str = Field(
        default="experiment",
        description="Project type: 'experiment' or 'default'",
    )


@register_tool
class CheckEvalConfigExistsTool(BaseTool):
    name = "check_eval_config_exists"
    description = (
        "Checks whether custom eval configurations already exist or conflict "
        "with existing ones on a project. Returns whether conflicts were found. "
        "Use before creating eval configs to avoid duplicates."
    )
    category = "tracing"
    input_model = CheckEvalConfigExistsInput

    def execute(
        self, params: CheckEvalConfigExistsInput, context: ToolContext
    ) -> ToolResult:

        from django.db.models import Q

        from tracer.models.custom_eval_config import CustomEvalConfig
        from tracer.models.project import Project

        # Check project exists
        try:
            Project.objects.get(
                name=params.project_name,
                organization=context.organization,
                trace_type=params.project_type,
            )
        except Project.DoesNotExist:
            return ToolResult(
                content=section(
                    "Config Check",
                    f"Project '{params.project_name}' does not exist yet. No conflicts.",
                ),
                data={
                    "exists": False,
                    "message": f"Project {params.project_name} does not exist",
                },
            )

        # Build conflict query for each eval_tag
        query = Q()
        for eval_tag in params.eval_tags:
            try:
                mapping_normalized = json.dumps(eval_tag.mapping, sort_keys=True)
                json_mapping = json.loads(mapping_normalized)
            except (json.JSONDecodeError, TypeError) as e:
                return ToolResult.error(
                    f"Invalid JSON in eval_tag mapping: {str(e)}",
                    error_code="VALIDATION_ERROR",
                )

            eval_query = Q(
                project__name=params.project_name,
                project__organization=context.organization,
                name=eval_tag.custom_eval_name,
            ) & (
                ~Q(mapping__exact=json_mapping)
                | ~Q(eval_template__name=eval_tag.eval_name)
            )
            query |= eval_query

        conflicting = CustomEvalConfig.objects.filter(query & Q(deleted=False)).first()

        if conflicting:
            info = key_value_block(
                [
                    ("Conflict Found", "Yes"),
                    ("Config Name", conflicting.name),
                    ("Config ID", f"`{conflicting.id}`"),
                    ("Project", params.project_name),
                    (
                        "Message",
                        f"Custom eval '{conflicting.name}' already exists with "
                        "different configuration or mapping",
                    ),
                ]
            )
            content = section("Config Check: Conflict Found", info)

            return ToolResult(
                content=content,
                data={
                    "exists": True,
                    "message": (
                        f"Custom eval '{conflicting.name}' already exists in "
                        f"project '{params.project_name}' with different "
                        "configuration or mapping"
                    ),
                    "conflicting_config_id": str(conflicting.id),
                },
            )

        content = section(
            "Config Check: No Conflicts",
            "All custom eval configurations are valid. No conflicts found.",
        )

        return ToolResult(
            content=content,
            data={
                "exists": False,
                "message": "All custom eval configurations are valid",
                "conflicting_config_id": None,
            },
        )
