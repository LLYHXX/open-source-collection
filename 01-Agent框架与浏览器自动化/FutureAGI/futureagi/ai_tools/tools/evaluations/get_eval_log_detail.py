from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    format_number,
    format_status,
    key_value_block,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetEvalLogDetailInput(PydanticBaseModel):
    log_id: UUID = Field(
        description="The UUID (log_id) of the eval log entry to retrieve"
    )


@register_tool
class GetEvalLogDetailTool(BaseTool):
    name = "get_eval_log_detail"
    description = (
        "Returns detailed information about a specific evaluation log entry "
        "including cost, status, token counts, configuration, and timestamps."
    )
    category = "evaluations"
    input_model = GetEvalLogDetailInput

    def execute(
        self, params: GetEvalLogDetailInput, context: ToolContext
    ) -> ToolResult:
        from tfc.ee_gating import EEFeature, is_oss

        if is_oss():
            return ToolResult.feature_unavailable(EEFeature.AUDIT_LOGS.value)

        from ee.usage.models.usage import APICallLog

        try:
            log = APICallLog.objects.get(
                log_id=params.log_id,
                organization=context.organization,
            )
        except APICallLog.DoesNotExist:
            return ToolResult.not_found("Eval Log", str(params.log_id))

        info = key_value_block(
            [
                ("Log ID", f"`{log.log_id}`"),
                ("Status", format_status(log.status)),
                ("Cost", format_number(log.cost, 6)),
                ("Deducted Cost", format_number(log.deducted_cost, 6)),
                ("Input Tokens", str(log.input_token_count or 0)),
                ("API Call Type", log.api_call_type.name if log.api_call_type else "—"),
                ("Source", log.source or "—"),
                ("Source ID", f"`{log.source_id}`" if log.source_id else "—"),
                ("Reference ID", f"`{log.reference_id}`" if log.reference_id else "—"),
                ("User", str(log.user) if log.user else "—"),
                ("Created", format_datetime(log.created_at)),
                ("Updated", format_datetime(log.updated_at)),
            ]
        )

        content = section("Eval Log Detail", info)

        # Show config if present
        if log.config and isinstance(log.config, dict) and log.config:
            content += "\n\n### Configuration\n\n"
            content += f"```json\n{truncate(str(log.config), 1000)}\n```"

        return ToolResult(
            content=content,
            data={
                "log_id": str(log.log_id),
                "status": log.status,
                "cost": str(log.cost),
                "deducted_cost": str(log.deducted_cost),
                "input_token_count": log.input_token_count,
                "api_call_type": log.api_call_type.name if log.api_call_type else None,
                "source": log.source,
                "source_id": log.source_id,
                "reference_id": log.reference_id,
                "config": log.config,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            },
        )
