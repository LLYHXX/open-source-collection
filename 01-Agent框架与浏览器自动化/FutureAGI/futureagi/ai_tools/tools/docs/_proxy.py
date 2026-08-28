"""Shared proxy for calling the docs-agent MCP server.

Uses a session pool to amortize the MCP initialize handshake across calls.
Each session is a lightweight string ID — the pool just avoids re-initializing
on every single tool call while staying safe for concurrent use.
"""

import json
import os
from collections import deque

import httpx
import structlog

logger = structlog.get_logger(__name__)

DOCS_AGENT_URL = os.environ.get("DOCS_AGENT_URL", "http://docs-agent:3002/mcp")
DOCS_AGENT_API_KEY = os.environ.get("DOCS_AGENT_API_KEY", "")


class MCPSessionPool:
    """Pool of MCP session IDs. Thread/async safe via deque (atomic append/pop)."""

    def __init__(self, max_size=5):
        self._pool = deque(maxlen=max_size)

    def acquire(self):
        """Get a session ID from the pool, or None if empty."""
        try:
            return self._pool.pop()
        except IndexError:
            return None

    def release(self, session_id):
        """Return a session ID to the pool."""
        if session_id:
            self._pool.append(session_id)

    def discard(self, session_id):
        """Drop a session (e.g. expired). Don't return to pool."""
        pass  # nothing to do — it's just not returned


_pool = MCPSessionPool()


def _headers(session_id=None):
    h = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if DOCS_AGENT_API_KEY:
        h["X-API-Key"] = DOCS_AGENT_API_KEY
    if session_id:
        h["mcp-session-id"] = session_id
    return h


def _initialize(client):
    """Create a new MCP session. Returns session ID."""
    resp = client.post(
        DOCS_AGENT_URL,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "falcon-ai", "version": "1.0.0"},
            },
        },
        headers=_headers(),
    )
    resp.raise_for_status()
    sid = resp.headers.get("mcp-session-id", "")

    # Send initialized notification
    client.post(
        DOCS_AGENT_URL,
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers=_headers(sid),
    )
    return sid


def _parse_response(resp):
    """Extract text content from an MCP response (JSON or SSE)."""
    content_type = resp.headers.get("content-type", "")

    if "text/event-stream" in content_type:
        for line in resp.text.split("\n"):
            if line.startswith("data: "):
                data = json.loads(line[6:])
                text_parts = [
                    b["text"]
                    for b in data.get("result", {}).get("content", [])
                    if b.get("type") == "text"
                ]
                if text_parts:
                    return "\n".join(text_parts)
        return None

    data = resp.json()
    result = data.get("result", {})
    text_parts = [
        b["text"] for b in result.get("content", []) if b.get("type") == "text"
    ]
    return "\n".join(text_parts) if text_parts else json.dumps(result)


def call_docs_agent(tool_name: str, arguments: dict) -> str | None:
    """Call a tool on the docs-agent MCP server.

    Acquires a session from the pool (or creates one), makes the call,
    and returns the session to the pool for reuse.
    """
    session_id = _pool.acquire()

    try:
        with httpx.Client(timeout=30.0) as client:
            # Initialize if no pooled session available
            if not session_id:
                session_id = _initialize(client)

            resp = client.post(
                DOCS_AGENT_URL,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                },
                headers=_headers(session_id),
            )

            # Session expired — discard, create fresh, retry
            if resp.status_code == 400:
                _pool.discard(session_id)
                session_id = _initialize(client)

                resp = client.post(
                    DOCS_AGENT_URL,
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": arguments},
                    },
                    headers=_headers(session_id),
                )

            resp.raise_for_status()
            result = _parse_response(resp)

            # Return session to pool for reuse
            _pool.release(session_id)
            return result

    except httpx.ConnectError:
        logger.warning("docs_agent_unavailable", url=DOCS_AGENT_URL)
        return None
    except Exception as e:
        logger.error("docs_agent_call_failed", error=str(e))
        # Don't return broken session to pool
        _pool.discard(session_id)
        return None
