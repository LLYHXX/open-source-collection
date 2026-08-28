from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    format_number,
    format_status,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetPromptExecutionResultsInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template")
    version_id: Optional[UUID] = Field(
        default=None,
        description="Filter by specific version UUID. If omitted, shows results for all versions.",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


@register_tool
class GetPromptExecutionResultsTool(BaseTool):
    name = "get_prompt_execution_results"
    description = (
        "Returns execution results for a prompt template, including API call logs "
        "and evaluation scores. Optionally filter by a specific prompt version."
    )
    category = "prompts"
    input_model = GetPromptExecutionResultsInput

    def execute(
        self, params: GetPromptExecutionResultsInput, context: ToolContext
    ) -> ToolResult:
        from tfc.ee_gating import EEFeature, is_oss

        if is_oss():
            return ToolResult.feature_unavailable(EEFeature.AUDIT_LOGS.value)

        from model_hub.models.run_prompt import PromptTemplate, PromptVersion
        from ee.usage.models.usage import APICallLog

        # Validate template
        try:
            template = PromptTemplate.objects.get(
                id=params.template_id,
                organization=context.organization,
                deleted=False,
            )
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        # If version_id specified, validate it
        version = None
        if params.version_id:
            try:
                version = PromptVersion.objects.get(
                    id=params.version_id,
                    original_template=template,
                    deleted=False,
                )
            except PromptVersion.DoesNotExist:
                return ToolResult.not_found("Prompt Version", str(params.version_id))

        # Query execution logs for the prompt template
        qs = APICallLog.objects.filter(
            organization=context.organization,
            source_id=str(params.template_id),
            source="prompt_bench",
        ).order_by("-created_at")

        if version:
            # Filter by reference_id if it stores the version ID
            qs = qs.filter(reference_id=str(version.id))

        total = qs.count()
        logs = qs[params.offset : params.offset + params.limit]

        # Also check for version-level evaluation results
        version_results = []
        if version and version.evaluation_results:
            for metric_name, result in version.evaluation_results.items():
                if isinstance(result, dict):
                    score = result.get("score", result.get("average", "—"))
                else:
                    score = result
                version_results.append({"metric": metric_name, "score": str(score)})

        if not logs and not version_results:
            content = section(
                f"Execution Results: {template.name}",
                "_No execution results found._",
            )
            if version:
                content += f"\n\n_Filtered by version: {version.template_version}_"
            return ToolResult(content=content, data={"results": [], "total": 0})

        content_parts = []

        # Show version evaluation results if available
        if version_results:
            eval_rows = [[r["metric"], r["score"]] for r in version_results]
            eval_table = markdown_table(["Metric", "Score"], eval_rows)
            content_parts.append(f"### Evaluation Scores\n\n{eval_table}")

        # Show execution logs
        if logs:
            rows = []
            data_list = []
            for log in logs:
                rows.append(
                    [
                        f"`{str(log.log_id)}`",
                        format_status(log.status),
                        format_number(log.cost, 6),
                        str(log.input_token_count or 0),
                        format_datetime(log.created_at),
                    ]
                )
                data_list.append(
                    {
                        "log_id": str(log.log_id),
                        "status": log.status,
                        "cost": str(log.cost),
                        "input_token_count": log.input_token_count,
                        "created_at": (
                            log.created_at.isoformat() if log.created_at else None
                        ),
                    }
                )

            table = markdown_table(
                ["Log ID", "Status", "Cost", "Tokens", "Created"],
                rows,
            )
            content_parts.append(f"### Execution Logs ({total})\n\n{table}")
        else:
            data_list = []

        header = f"Execution Results: {template.name}"
        if version:
            header += f" ({version.template_version})"

        content = section(header, "\n\n".join(content_parts))

        if total > params.offset + params.limit:
            content += f"\n\n_Use offset={params.offset + params.limit} to see more._"

        return ToolResult(
            content=content,
            data={
                "template_id": str(template.id),
                "version_id": str(version.id) if version else None,
                "logs": data_list,
                "evaluation_results": version_results,
                "total": total,
            },
        )
