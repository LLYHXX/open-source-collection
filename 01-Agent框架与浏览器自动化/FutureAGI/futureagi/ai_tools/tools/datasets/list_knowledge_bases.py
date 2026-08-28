from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    markdown_table,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class ListKnowledgeBasesInput(PydanticBaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


@register_tool
class ListKnowledgeBasesTool(BaseTool):
    name = "list_knowledge_bases"
    description = (
        "Lists knowledge bases in the workspace. Knowledge bases store "
        "document embeddings for RAG (Retrieval Augmented Generation) workflows."
    )
    category = "datasets"
    input_model = ListKnowledgeBasesInput

    def execute(
        self, params: ListKnowledgeBasesInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.kb import KnowledgeBase

        qs = KnowledgeBase.objects.order_by("-created_at")

        total = qs.count()
        kbs = qs[params.offset : params.offset + params.limit]

        rows = []
        data_list = []
        for kb in kbs:
            rows.append(
                [
                    f"`{kb.id}`",
                    truncate(kb.name, 40),
                    kb.embedding_model or "—",
                    str(kb.chunk_size) if kb.chunk_size else "—",
                    format_datetime(kb.created_at),
                ]
            )
            data_list.append(
                {
                    "id": str(kb.id),
                    "name": kb.name,
                    "embedding_model": kb.embedding_model,
                    "chunk_size": kb.chunk_size,
                }
            )

        table = markdown_table(
            ["ID", "Name", "Embedding Model", "Chunk Size", "Created"], rows
        )

        showing = f"Showing {len(rows)} of {total}"
        content = section(f"Knowledge Bases ({total})", f"{showing}\n\n{table}")

        if total > params.offset + params.limit:
            content += (
                f"\n\n_Use offset={params.offset + params.limit} to see more results._"
            )

        return ToolResult(
            content=content, data={"knowledge_bases": data_list, "total": total}
        )
