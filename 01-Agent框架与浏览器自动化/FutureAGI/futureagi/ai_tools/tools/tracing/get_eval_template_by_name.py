from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetEvalTemplateByNameInput(PydanticBaseModel):
    eval_template_name: str = Field(
        description="The name of the eval template to look up",
        min_length=1,
    )


@register_tool
class GetEvalTemplateByNameTool(BaseTool):
    name = "get_eval_template_by_name"
    description = (
        "Looks up a user-created eval template by name. Returns template details "
        "if found, or indicates it is not a user template. Useful for checking "
        "if a custom eval template exists before creating configs."
    )
    category = "tracing"
    input_model = GetEvalTemplateByNameInput

    def execute(
        self, params: GetEvalTemplateByNameInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.choices import OwnerChoices
        from model_hub.models.evals_metric import EvalTemplate

        try:
            template = EvalTemplate.objects.get(
                name=params.eval_template_name,
                organization=context.organization,
                owner=OwnerChoices.USER.value,
            )
        except EvalTemplate.DoesNotExist:
            return ToolResult(
                content=section(
                    "Eval Template Lookup",
                    f"No user-created eval template named "
                    f"'{params.eval_template_name}' found. "
                    "It may be a system template or does not exist.",
                ),
                data={
                    "is_user_eval_template": False,
                    "eval_template": None,
                },
            )

        description = getattr(template, "description", None) or "—"
        criteria = getattr(template, "criteria", None)

        info = key_value_block(
            [
                ("Template ID", f"`{template.id}`"),
                ("Name", template.name),
                ("Description", description),
                ("Owner", template.owner),
                (
                    "Config",
                    truncate(str(template.config), 300) if template.config else "—",
                ),
                (
                    "Criteria",
                    truncate(criteria, 200) if criteria else "—",
                ),
                ("Is User Template", "Yes"),
            ]
        )

        content = section(f"Eval Template: {template.name}", info)

        return ToolResult(
            content=content,
            data={
                "is_user_eval_template": True,
                "eval_template": {
                    "id": str(template.id),
                    "name": template.name,
                    "description": description,
                    "config": template.config,
                    "criteria": criteria,
                },
            },
        )
