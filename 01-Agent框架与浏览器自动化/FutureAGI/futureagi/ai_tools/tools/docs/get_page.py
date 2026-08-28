import structlog
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.registry import register_tool
from ai_tools.tools.docs._proxy import call_docs_agent

logger = structlog.get_logger(__name__)


class GetPageInput(PydanticBaseModel):
    path: str = Field(
        description=(
            "Documentation page path, e.g., 'tracing/auto-overview' "
            "or 'dataset/overview'"
        )
    )


@register_tool
class GetPageTool(BaseTool):
    name = "get_docs_page"
    description = (
        "Get a specific documentation page by path. Use when you know "
        "the exact page the user needs."
    )
    category = "docs"
    input_model = GetPageInput

    def execute(self, params: GetPageInput, context: ToolContext) -> ToolResult:
        try:
            result = call_docs_agent(
                "get_page",
                {"path": params.path},
            )
            if result is None:
                return ToolResult(
                    content=(
                        "Documentation service is currently unavailable. "
                        "Please try again later or visit https://docs.futureagi.com"
                    ),
                    is_error=True,
                    error_code="SERVICE_UNAVAILABLE",
                )
            return ToolResult(content=result, data={"source": "docs-agent"})
        except Exception as e:
            logger.error("get_docs_page_error", error=str(e))
            return ToolResult(
                content=(
                    f"Failed to fetch documentation page: {e}. "
                    "Visit https://docs.futureagi.com for help."
                ),
                is_error=True,
            )
