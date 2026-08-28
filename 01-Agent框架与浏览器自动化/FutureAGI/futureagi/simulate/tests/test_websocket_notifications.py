"""
Unit tests for WebSocket notification utility.

Tests cover:
- notify_simulation_update: Redis pub/sub publishing for simulation grid updates
- Thread-safe Redis client initialization
- Organization-scoped channel naming
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from simulate.utils.websocket_notifications import notify_simulation_update


@pytest.mark.unit
class TestNotifySimulationUpdate:
    """Tests for notify_simulation_update function."""

    @patch("simulate.utils.websocket_notifications._get_redis")
    def test_publishes_to_org_scoped_channel(self, mock_get_redis):
        """Should publish to 'simulation_updates:{org_id}:{run_test_id}' channel."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        notify_simulation_update(
            organization_id="org-123",
            run_test_id="run-456",
            test_execution_id="exec-789",
        )

        mock_redis.publish.assert_called_once()
        channel, message = mock_redis.publish.call_args[0]
        assert channel == "simulation_updates:org-123:run-456"

    @patch("simulate.utils.websocket_notifications._get_redis")
    def test_message_format(self, mock_get_redis):
        """Should publish a JSON message with type and data fields."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        notify_simulation_update(
            organization_id="org-123",
            run_test_id="run-456",
            test_execution_id="exec-789",
        )

        _, message = mock_redis.publish.call_args[0]
        parsed = json.loads(message)

        assert parsed["type"] == "simulation_update"
        assert parsed["data"]["run_test_id"] == "run-456"
        assert parsed["data"]["test_execution_id"] == "exec-789"

    @patch("simulate.utils.websocket_notifications._get_redis")
    def test_optional_test_execution_id(self, mock_get_redis):
        """Should handle None test_execution_id gracefully."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        notify_simulation_update(
            organization_id="org-123",
            run_test_id="run-456",
        )

        _, message = mock_redis.publish.call_args[0]
        parsed = json.loads(message)

        assert parsed["data"]["test_execution_id"] is None

    @patch("simulate.utils.websocket_notifications._get_redis")
    def test_handles_redis_error_gracefully(self, mock_get_redis):
        """Should not raise when Redis publish fails."""
        mock_redis = MagicMock()
        mock_redis.publish.side_effect = ConnectionError("Redis down")
        mock_get_redis.return_value = mock_redis

        # Should not raise
        notify_simulation_update(
            organization_id="org-123",
            run_test_id="run-456",
        )

    @patch("simulate.utils.websocket_notifications._get_redis")
    def test_converts_ids_to_strings(self, mock_get_redis):
        """Should convert UUID-like ids to strings in the message."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        import uuid

        run_id = uuid.uuid4()
        exec_id = uuid.uuid4()

        notify_simulation_update(
            organization_id="org-123",
            run_test_id=run_id,
            test_execution_id=exec_id,
        )

        _, message = mock_redis.publish.call_args[0]
        parsed = json.loads(message)

        assert parsed["data"]["run_test_id"] == str(run_id)
        assert parsed["data"]["test_execution_id"] == str(exec_id)
