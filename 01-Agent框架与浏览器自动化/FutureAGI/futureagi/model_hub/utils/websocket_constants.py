"""
WebSocket constants for consistent communication between frontend and backend
"""


# WebSocket message types
class WebSocketMessageType:
    RUN_PROMPT = "run_prompt"
    GENERATE_PROMPT = "generate_prompt"
    IMPROVE_PROMPT = "improve_prompt"
    STOP_STREAMING = "stop_streaming"
    SESSION_UUID = "session_uuid"
    ERROR = "error"
    COMPLETED = "completed"
    CHUNK = "chunk"


# WebSocket status types
class WebSocketStatus:
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"
    ALL_COMPLETED = "all_completed"
    PROCESS_STARTED = "process_started"


# WebSocket payload structure
class WebSocketPayload:
    """Standard WebSocket payload structure"""

    @staticmethod
    def create_streaming_payload(
        message_type: str,
        streaming_status: str,
        version: str,
        session_uuid: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Create a standardized streaming payload

        Args:
            message_type: Type of message (e.g., WebSocketMessageType.RUN_PROMPT)
            streaming_status: Status of streaming (e.g., WebSocketStatus.RUNNING)
            version: Version string
            session_uuid: Unique session UUID for tracking
            **kwargs: Additional payload data

        Returns:
            Standardized payload dictionary
        """
        import time

        payload = {
            "type": message_type,
            "streaming_status": streaming_status,
            "version": version,
            "timestamp": time.time(),
        }

        # Add session UUID if provided
        if session_uuid:
            payload["session_uuid"] = session_uuid

        # Add additional data
        payload.update(kwargs)

        return payload

    @staticmethod
    def create_error_payload(
        message_type: str,
        error: str,
        version: str | None = None,
        session_uuid: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Create a standardized error payload

        Args:
            message_type: Type of message
            error: Error message
            version: Version string (optional)
            session_uuid: Unique session UUID for tracking
            **kwargs: Additional payload data

        Returns:
            Standardized error payload dictionary
        """
        import time

        payload = {
            "type": message_type,
            "streaming_status": WebSocketStatus.ERROR,
            "error": error,
            "timestamp": time.time(),
        }

        if version:
            payload["version"] = version

        # Add session UUID if provided
        if session_uuid:
            payload["session_uuid"] = session_uuid

        # Add additional data
        payload.update(kwargs)

        return payload


# Cache key patterns
class CacheKeyPatterns:
    """Standard cache key patterns for WebSocket operations"""

    STOP_STREAMING = "stop_streaming_{template_id}_{version}"
    PROMPT_TEMPLATE_RESPONSE = (
        "prompt_template_{template_id}_{version}_run_prompt_{index}"
    )
    WEBSOCKET_SESSION = "websocket_session_{organization_id}_{template_id}"
    STOP_SESSION_UUID = "stop_session_uuid_{session_uuid}"
    ACTIVE_SESSION_UUIDS = "active_session_uuids_{template_id}_{version}"


# Error messages
class WebSocketErrorMessages:
    """Standard error messages for WebSocket operations"""

    CONNECTION_FAILED = "WebSocket connection failed"
    MESSAGE_SEND_FAILED = "Failed to send WebSocket message"
    INVALID_PAYLOAD = "Invalid WebSocket payload"
    STREAMING_STOPPED = "Streaming has been stopped"
    TEMPLATE_NOT_FOUND = "Template not found"
    VERSION_NOT_FOUND = "Version not found"
    ORGANIZATION_NOT_FOUND = "Organization not found"
