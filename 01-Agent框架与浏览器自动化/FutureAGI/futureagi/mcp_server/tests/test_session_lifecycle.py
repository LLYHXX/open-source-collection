"""Tests for SSE session lifecycle: heartbeat, disconnect, stale cleanup."""

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from django.utils import timezone

from mcp_server.models.session import MCPSession
from mcp_server.session_manager import (
    HEARTBEAT_INTERVAL,
    STALE_SESSION_HOURS,
    _active_heartbeats,
    _mark_disconnected,
    cleanup_stale_sessions,
    start_heartbeat,
    stop_heartbeat,
)
from mcp_server.sse_lifecycle import on_sse_connect, on_sse_disconnect


@pytest.mark.django_db
class TestCleanupStaleSessions:
    """Tests for cleanup_stale_sessions()."""

    def test_marks_old_active_sessions_as_disconnected(self, mcp_session):
        """Sessions with last_activity_at older than STALE_SESSION_HOURS get disconnected."""
        cutoff = timezone.now() - timedelta(hours=STALE_SESSION_HOURS + 1)
        MCPSession.objects.filter(id=mcp_session.id).update(
            last_activity_at=cutoff, status="active"
        )

        cleanup_stale_sessions()

        mcp_session.refresh_from_db()
        assert mcp_session.status == "disconnected"
        assert mcp_session.ended_at is not None

    def test_does_not_touch_recent_sessions(self, mcp_session):
        """Active sessions with recent activity are left alone."""
        MCPSession.objects.filter(id=mcp_session.id).update(
            last_activity_at=timezone.now(), status="active"
        )

        cleanup_stale_sessions()

        mcp_session.refresh_from_db()
        assert mcp_session.status == "active"
        assert mcp_session.ended_at is None

    def test_does_not_touch_non_active_sessions(self, mcp_session):
        """Already-disconnected sessions are not modified."""
        cutoff = timezone.now() - timedelta(hours=STALE_SESSION_HOURS + 1)
        MCPSession.objects.filter(id=mcp_session.id).update(
            last_activity_at=cutoff, status="disconnected"
        )

        cleanup_stale_sessions()

        mcp_session.refresh_from_db()
        assert mcp_session.status == "disconnected"


@pytest.mark.django_db
class TestMarkDisconnected:
    """Tests for _mark_disconnected()."""

    def test_updates_status_and_ended_at(self, mcp_session):
        """Active session gets status=disconnected and ended_at set."""
        assert mcp_session.status == "active"
        assert mcp_session.ended_at is None

        _mark_disconnected(str(mcp_session.id))

        mcp_session.refresh_from_db()
        assert mcp_session.status == "disconnected"
        assert mcp_session.ended_at is not None

    def test_ignores_non_active_sessions(self, mcp_session):
        """Sessions not in 'active' status are not modified."""
        MCPSession.objects.filter(id=mcp_session.id).update(status="revoked")

        _mark_disconnected(str(mcp_session.id))

        mcp_session.refresh_from_db()
        assert mcp_session.status == "revoked"
        assert mcp_session.ended_at is None


@pytest.mark.asyncio
class TestStartHeartbeat:
    """Tests for start_heartbeat()."""

    async def test_creates_asyncio_task(self):
        """start_heartbeat should create and register an asyncio task."""
        session_id = "test-hb-001"
        _active_heartbeats.pop(session_id, None)

        task = await start_heartbeat(session_id)
        try:
            assert isinstance(task, asyncio.Task)
            assert session_id in _active_heartbeats
            assert _active_heartbeats[session_id] is task
        finally:
            task.cancel()
            _active_heartbeats.pop(session_id, None)
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def test_heartbeat_interval_constant(self):
        """Sanity check the heartbeat interval is reasonable."""
        assert HEARTBEAT_INTERVAL == 30


@pytest.mark.asyncio
class TestStopHeartbeat:
    """Tests for stop_heartbeat()."""

    async def test_cancels_task_and_marks_disconnected(self):
        """stop_heartbeat cancels the task and calls _mark_disconnected."""
        session_id = "test-stop-001"

        # Create a dummy long-running task
        async def _dummy():
            await asyncio.sleep(3600)

        task = asyncio.create_task(_dummy())
        _active_heartbeats[session_id] = task

        with patch("mcp_server.session_manager._mark_disconnected") as mock_mark:
            await stop_heartbeat(session_id)

            assert task.cancelled()
            assert session_id not in _active_heartbeats
            mock_mark.assert_called_once_with(session_id)

    async def test_noop_for_unknown_session(self):
        """stop_heartbeat for an unknown session_id should not raise."""
        with patch("mcp_server.session_manager._mark_disconnected"):
            await stop_heartbeat("nonexistent-session")
        # No exception = pass


@pytest.mark.asyncio
class TestSSELifecycleHooks:
    """Tests for on_sse_connect() and on_sse_disconnect()."""

    async def test_on_sse_connect_starts_heartbeat_and_cleans(self):
        """on_sse_connect should cleanup stale sessions then start heartbeat."""
        session_id = "test-connect-001"

        with (
            patch("mcp_server.sse_lifecycle.cleanup_stale_sessions") as mock_cleanup,
            patch(
                "mcp_server.sse_lifecycle.start_heartbeat",
                new_callable=AsyncMock,
            ) as mock_start,
        ):
            await on_sse_connect(session_id)

            mock_cleanup.assert_called_once()
            mock_start.assert_awaited_once_with(session_id)

    async def test_on_sse_disconnect_stops_heartbeat(self):
        """on_sse_disconnect should stop heartbeat for the session."""
        session_id = "test-disconnect-001"

        with patch(
            "mcp_server.sse_lifecycle.stop_heartbeat",
            new_callable=AsyncMock,
        ) as mock_stop:
            await on_sse_disconnect(session_id)

            mock_stop.assert_awaited_once_with(session_id)
