from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import section
from ai_tools.registry import register_tool


class DeleteEvalLogsInput(PydanticBaseModel):
    log_ids: list[UUID] = Field(
        description="List of log_id UUIDs to delete",
        min_length=1,
    )


@register_tool
class DeleteEvalLogsTool(BaseTool):
    name = "delete_eval_logs"
    description = (
        "Deletes evaluation log entries by their log IDs. "
        "This permanently removes the API call log records. "
        "Use get_eval_logs to find log IDs first."
    )
    category = "evaluations"
    input_model = DeleteEvalLogsInput

    def execute(self, params: DeleteEvalLogsInput, context: ToolContext) -> ToolResult:
        from tfc.ee_gating import EEFeature, is_oss

        if is_oss():
            return ToolResult.feature_unavailable(EEFeature.AUDIT_LOGS.value)

        from ee.usage.models.usage import APICallLog

        # Find matching logs belonging to this organization
        log_id_strs = [str(lid) for lid in params.log_ids]
        logs = APICallLog.objects.filter(
            log_id__in=log_id_strs,
            organization=context.organization,
        )

        found_ids = set(str(log.log_id) for log in logs)
        missing = [lid for lid in log_id_strs if lid not in found_ids]

        if not logs.exists():
            return ToolResult.error(
                "No matching log entries found for the provided IDs in this organization.",
                error_code="NOT_FOUND",
            )

        count = logs.count()
        logs.delete()

        content = section(
            "Eval Logs Deleted",
            f"Successfully deleted **{count}** log entry(ies).",
        )

        if missing:
            content += (
                f"\n\n_Note: {len(missing)} log ID(s) were not found and skipped._"
            )

        return ToolResult(
            content=content,
            data={
                "deleted_count": count,
                "missing_ids": missing,
            },
        )
