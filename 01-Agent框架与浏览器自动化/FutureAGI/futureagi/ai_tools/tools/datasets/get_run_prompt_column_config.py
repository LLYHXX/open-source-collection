from uuid import UUID

import structlog
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import dashboard_link, key_value_block, section
from ai_tools.registry import register_tool

logger = structlog.get_logger(__name__)


class GetRunPromptColumnConfigInput(PydanticBaseModel):
    column_id: UUID = Field(description="The UUID of the run-prompt column")


@register_tool
class GetRunPromptColumnConfigTool(BaseTool):
    name = "get_run_prompt_column_config"
    description = (
        "Retrieves the full configuration of an existing run-prompt column, "
        "including model, messages, parameters, tools, and status."
    )
    category = "datasets"
    input_model = GetRunPromptColumnConfigInput

    def execute(
        self, params: GetRunPromptColumnConfigInput, context: ToolContext
    ) -> ToolResult:
        from model_hub.models.choices import SourceChoices
        from model_hub.models.develop_dataset import Column
        from model_hub.models.run_prompt import RunPrompter

        # Validate column exists
        try:
            column = Column.objects.select_related("dataset").get(
                id=params.column_id, deleted=False
            )
        except Column.DoesNotExist:
            return ToolResult.not_found("Column", str(params.column_id))

        # Organization check via column's dataset
        if column.dataset.organization_id != context.organization.id:
            return ToolResult.not_found("Column", str(params.column_id))

        if column.source != SourceChoices.RUN_PROMPT.value:
            return ToolResult.error(
                f"Column '{column.name}' is not a run-prompt column (source: {column.source}).",
                error_code="VALIDATION_ERROR",
            )

        # Get RunPrompter config
        try:
            rp = RunPrompter.objects.get(id=column.source_id)
        except RunPrompter.DoesNotExist:
            return ToolResult.error(
                "Run prompt configuration not found for this column.",
                error_code="NOT_FOUND",
            )

        dataset = column.dataset

        # Build messages summary
        messages_summary = []
        for i, msg in enumerate(rp.messages or []):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if len(content) > 200:
                content = content[:200] + "..."
            messages_summary.append(f"  {i + 1}. **{role}**: {content}")

        # Build tools list
        tools_info = []
        for tool in rp.tools.all():
            tools_info.append(f"  - `{tool.id}` ({tool.name})")

        info = key_value_block(
            [
                ("Column ID", f"`{column.id}`"),
                ("Column Name", rp.name),
                ("RunPrompter ID", f"`{rp.id}`"),
                ("Model", rp.model),
                ("Status", rp.status),
                ("Output Format", rp.output_format or "string"),
                (
                    "Temperature",
                    str(rp.temperature) if rp.temperature is not None else "default",
                ),
                ("Max Tokens", str(rp.max_tokens) if rp.max_tokens else "default"),
                ("Top P", str(rp.top_p) if rp.top_p is not None else "default"),
                (
                    "Frequency Penalty",
                    (
                        str(rp.frequency_penalty)
                        if rp.frequency_penalty is not None
                        else "default"
                    ),
                ),
                (
                    "Presence Penalty",
                    (
                        str(rp.presence_penalty)
                        if rp.presence_penalty is not None
                        else "default"
                    ),
                ),
                ("Concurrency", str(rp.concurrency)),
                ("Tool Choice", rp.tool_choice or "none"),
                (
                    "Dataset",
                    dashboard_link("dataset", str(dataset.id), label=dataset.name),
                ),
            ]
        )

        content = section("Run Prompt Column Config", info)

        if messages_summary:
            content += "\n\n### Messages\n" + "\n".join(messages_summary)

        if tools_info:
            content += "\n\n### Tools\n" + "\n".join(tools_info)

        # Build data dict with full config
        data = {
            "column_id": str(column.id),
            "run_prompter_id": str(rp.id),
            "dataset_id": str(dataset.id),
            "name": rp.name,
            "model": rp.model,
            "status": rp.status,
            "output_format": rp.output_format,
            "temperature": rp.temperature,
            "max_tokens": rp.max_tokens,
            "top_p": rp.top_p,
            "frequency_penalty": rp.frequency_penalty,
            "presence_penalty": rp.presence_penalty,
            "concurrency": rp.concurrency,
            "tool_choice": rp.tool_choice,
            "response_format": rp.response_format,
            "messages": rp.messages,
            "run_prompt_config": rp.run_prompt_config,
            "tools": [str(t.id) for t in rp.tools.all()],
        }

        return ToolResult(content=content, data=data)
