from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetPromptEvalConfigsInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template")


@register_tool
class GetPromptEvalConfigsTool(BaseTool):
    name = "get_prompt_eval_configs"
    description = (
        "Returns evaluation configurations set up for a prompt template. "
        "Shows each eval metric, its mapping, model, and status."
    )
    category = "prompts"
    input_model = GetPromptEvalConfigsInput

    def execute(
        self, params: GetPromptEvalConfigsInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.run_prompt import PromptEvalConfig, PromptTemplate

        try:
            template = PromptTemplate.objects.get(id=params.template_id)
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        configs = PromptEvalConfig.objects.filter(
            prompt_template=template, deleted=False
        ).select_related("eval_template", "eval_group")

        if not configs.exists():
            return ToolResult(
                content=section(
                    f"Eval Configs: {template.name}",
                    "_No evaluation configs found._",
                ),
                data={"configs": []},
            )

        rows = []
        data_list = []
        for cfg in configs:
            eval_name = cfg.eval_template.name if cfg.eval_template else "—"
            group_name = cfg.eval_group.name if cfg.eval_group else "—"
            mapping_str = truncate(str(cfg.mapping), 40) if cfg.mapping else "—"

            model_name = (
                cfg.eval_template.model
                if cfg.eval_template and cfg.eval_template.model
                else "—"
            )

            rows.append(
                [
                    cfg.name or eval_name,
                    eval_name,
                    group_name,
                    model_name,
                    mapping_str,
                    "Active" if not cfg.deleted else "Deleted",
                ]
            )
            data_list.append(
                {
                    "id": str(cfg.id),
                    "name": cfg.name or eval_name,
                    "eval_template_id": (
                        str(cfg.eval_template_id) if cfg.eval_template_id else None
                    ),
                    "eval_template_name": eval_name,
                    "group": group_name,
                    "model": model_name,
                    "mapping": cfg.mapping,
                    "config": cfg.config,
                    "error_localizer": cfg.error_localizer,
                }
            )

        table = markdown_table(
            ["Name", "Template", "Group", "Model", "Mapping", "Status"],
            rows,
        )

        content = section(f"Eval Configs: {template.name} ({len(data_list)})", table)

        return ToolResult(content=content, data={"configs": data_list})
