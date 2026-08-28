"""Pydantic schemas for integration export data."""

import time as time_module

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field


class ExportEvent(PydanticBaseModel):
    """Common event format for PostHog and Mixpanel exports."""

    event: str = "agentcc_request"
    timestamp: str = ""
    time: int = Field(default_factory=lambda: int(time_module.time()))
    distinct_id: str = "agentcc-gateway"
    properties: dict = Field(default_factory=dict)

    @classmethod
    def from_request_log(cls, log) -> "ExportEvent":
        ts = log.started_at or log.created_at
        return cls(
            timestamp=ts.isoformat() if ts else "",
            time=int(ts.timestamp()) if ts else int(time_module.time()),
            distinct_id=log.user_id or "agentcc-gateway",
            properties={
                "request_id": log.request_id,
                "model": log.model,
                "provider": log.provider,
                "resolved_model": log.resolved_model,
                "latency_ms": log.latency_ms,
                "input_tokens": log.input_tokens,
                "output_tokens": log.output_tokens,
                "total_tokens": log.total_tokens,
                "cost": float(log.cost) if log.cost else 0,
                "status_code": log.status_code,
                "is_stream": log.is_stream,
                "is_error": log.is_error,
                "cache_hit": log.cache_hit,
                "fallback_used": log.fallback_used,
                "guardrail_triggered": log.guardrail_triggered,
            },
        )


class ExportLogRecord(PydanticBaseModel):
    """Flat log record for Cloud Storage and Message Queue exports."""

    request_id: str = ""
    model: str = ""
    provider: str = ""
    resolved_model: str = ""
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0
    status_code: int = 0
    is_stream: bool = False
    is_error: bool = False
    error_message: str = ""
    cache_hit: bool = False
    fallback_used: bool = False
    guardrail_triggered: bool = False
    routing_strategy: str = ""
    timestamp: str = ""
    event_type: str = "request"

    @classmethod
    def from_request_log(cls, log) -> "ExportLogRecord":
        ts = log.started_at or log.created_at
        return cls(
            request_id=log.request_id,
            model=log.model,
            provider=log.provider,
            resolved_model=log.resolved_model,
            latency_ms=log.latency_ms,
            input_tokens=log.input_tokens,
            output_tokens=log.output_tokens,
            total_tokens=log.total_tokens,
            cost=float(log.cost) if log.cost else 0,
            status_code=log.status_code,
            is_stream=log.is_stream,
            is_error=log.is_error,
            error_message=(log.error_message[:500] if log.error_message else ""),
            cache_hit=log.cache_hit,
            fallback_used=log.fallback_used,
            guardrail_triggered=log.guardrail_triggered,
            routing_strategy=log.routing_strategy,
            timestamp=ts.isoformat() if ts else "",
        )
