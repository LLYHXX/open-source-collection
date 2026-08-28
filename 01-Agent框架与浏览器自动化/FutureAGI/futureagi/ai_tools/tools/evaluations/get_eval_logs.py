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


class GetEvalLogsInput(PydanticBaseModel):
    eval_template_id: UUID = Field(
        description="The UUID of the eval template to get logs for"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    search: Optional[str] = Field(
        default=None,
        description="Search/filter logs by status or source",
    )


@register_tool
class GetEvalLogsTool(BaseTool):
    name = "get_eval_logs"
    description = (
        "Returns evaluation execution logs/history for a specific eval template. "
        "Shows API call logs including cost, status, timestamps, and token counts."
    )
    category = "evaluations"
    input_model = GetEvalLogsInput

    def execute(self, params: GetEvalLogsInput, context: ToolContext) -> ToolResult:
        from tfc.ee_gating import EEFeature, is_oss

        if is_oss():
            return ToolResult.feature_unavailable(EEFeature.AUDIT_LOGS.value)

        from model_hub.models.evals_metric import EvalTemplate
        from model_hub.utils.eval_validators import validate_eval_template_org_access
        from ee.usage.models.usage import APICallLog

        # Validate template exists and belongs to org
        try:
            template = validate_eval_template_org_access(
                params.eval_template_id, context.organization
            )
        except EvalTemplate.DoesNotExist:
            return ToolResult.not_found("Eval Template", str(params.eval_template_id))

        # Query logs: source_id stores the eval template ID
        qs = APICallLog.objects.filter(
            organization=context.organization,
            source_id=str(params.eval_template_id),
        ).order_by("-created_at")

        if params.search:
            from django.db.models import Q

            qs = qs.filter(
                Q(status__icontains=params.search) | Q(source__icontains=params.search)
            )

        total = qs.count()
        logs = qs[params.offset : params.offset + params.limit]

        if not logs:
            return ToolResult(
                content=section(
                    f"Eval Logs: {template.name}",
                    "_No execution logs found for this eval template._",
                ),
                data={"logs": [], "total": 0},
            )

        rows = []
        data_list = []
        for log in logs:
            rows.append(
                [
                    f"`{str(log.log_id)}`",
                    format_status(log.status),
                    format_number(log.cost, 6),
                    str(log.input_token_count or 0),
                    log.source or "—",
                    format_datetime(log.created_at),
                ]
            )
            data_list.append(
                {
                    "log_id": str(log.log_id),
                    "status": log.status,
                    "cost": str(log.cost),
                    "input_token_count": log.input_token_count,
                    "source": log.source,
                    "created_at": (
                        log.created_at.isoformat() if log.created_at else None
                    ),
                }
            )

        table = markdown_table(
            ["Log ID", "Status", "Cost", "Tokens", "Source", "Created"],
            rows,
        )

        showing = f"Showing {len(rows)} of {total}"
        content = section(
            f"Eval Logs: {template.name} ({total})", f"{showing}\n\n{table}"
        )

        if total > params.offset + params.limit:
            content += f"\n\n_Use offset={params.offset + params.limit} to see more._"

        return ToolResult(content=content, data={"logs": data_list, "total": total})
