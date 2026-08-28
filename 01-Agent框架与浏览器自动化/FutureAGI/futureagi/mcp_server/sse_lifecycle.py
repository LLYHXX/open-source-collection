"""SSE connection lifecycle hooks -- called from mcp_app.py."""

import structlog
from asgiref.sync import sync_to_async

from mcp_server.session_manager import (
    cleanup_stale_sessions,
    start_heartbeat,
    stop_heartbeat,
)

logger = structlog.get_logger(__name__)


async def on_sse_connect(session_id: str):
    """Called when an SSE client connects. Starts heartbeat and cleans stale sessions."""
    await sync_to_async(cleanup_stale_sessions)()
    await start_heartbeat(session_id)
    logger.info("sse_connected", session_id=session_id)


async def on_sse_disconnect(session_id: str):
    """Called when an SSE client disconnects. Stops heartbeat and marks session disconnected."""
    await stop_heartbeat(session_id)
    logger.info("sse_disconnected", session_id=session_id)
