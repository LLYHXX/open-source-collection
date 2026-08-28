from typing import Any

from pydantic import BaseModel, Field


class FetchPromptMetricsRequest(BaseModel):
    """
    Pydantic model for fetch_prompt_metrics request validation.

    This model validates the input parameters for fetching prompt metrics,
    ensuring proper data types and required fields.
    """

    prompt_template_id: str = Field(
        ...,
        description="Unique identifier for the prompt template",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    )
    filters: list[dict[str, Any]] | None = Field(
        default_factory=list,
        description="Optional filters to apply when fetching metrics",
    )
    organization_id: str = Field(
        ...,
        description="Unique identifier for the organisation",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    )

    search_term: str | None = Field(
        default=None, description="Optional search term to apply when fetching metrics"
    )

    page_number: int | None = Field(
        default=0, description="Optional page number to apply when fetching metrics"
    )
    page_size: int | None = Field(
        default=10, description="Optional page size to apply when fetching metrics"
    )
