"""SSE session lifecycle management -- heartbeat, disconnect cleanup, stale detection."""

import asyncio
from datetime import timedelta

import structlog
from asgiref.sync import sync_to_async
from django.utils import timezone

logger = structlog.get_logger(__name__)

# Track active SSE sessions: session_id -> asyncio.Task (heartbeat)
_active_heartbeats: dict[str, asyncio.Task] = {}

HEARTBEAT_INTERVAL = 30  # seconds
STALE_SESSION_HOURS = 24  # mark sessions stale after this long


async def start_heartbeat(session_id: str) -> asyncio.Task:
    """Start periodic heartbeat for an SSE session."""

    async def _heartbeat_loop():
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            try:
                await sync_to_async(_update_activity)(session_id)
            except Exception:
                logger.warning("heartbeat_update_failed", session_id=session_id)
                break

    task = asyncio.create_task(_heartbeat_loop())
    _active_heartbeats[session_id] = task
    return task


def _update_activity(session_id: str):
    """Update session last_activity_at (sync, called via sync_to_async)."""
    from mcp_server.models.session import MCPSession

    try:
        MCPSession.objects.filter(id=session_id, status="active").update(
            last_activity_at=timezone.now()
        )
    except Exception:
        pass


async def stop_heartbeat(session_id: str):
    """Stop heartbeat and mark session as disconnected."""
    task = _active_heartbeats.pop(session_id, None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await sync_to_async(_mark_disconnected)(session_id)


def _mark_disconnected(session_id: str):
    """Mark a session as disconnected with ended_at timestamp."""
    from mcp_server.models.session import MCPSession

    MCPSession.objects.filter(id=session_id, status="active").update(
        status="disconnected",
        ended_at=timezone.now(),
    )


def cleanup_stale_sessions():
    """Mark old active sessions as disconnected (sync)."""
    from mcp_server.models.session import MCPSession

    cutoff = timezone.now() - timedelta(hours=STALE_SESSION_HOURS)
    stale_count = MCPSession.objects.filter(
        status="active",
        last_activity_at__lt=cutoff,
    ).update(
        status="disconnected",
        ended_at=timezone.now(),
    )
    if stale_count:
        logger.info("cleaned_stale_sessions", count=stale_count)
