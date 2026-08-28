import time
import uuid
from typing import Any

import structlog
from django.core.cache import cache

logger = structlog.get_logger(__name__)
from model_hub.utils import call_websocket
from model_hub.utils.websocket_constants import (
    CacheKeyPatterns,
    WebSocketMessageType,
    WebSocketPayload,
    WebSocketStatus,
)


class WebSocketManager:
    """Centralized WebSocket manager for consistent payload handling and streaming control"""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self._cache_timeout = 10 * 60  # 10 minutes
        # Generate unique UUID for this WebSocket manager instance
        self.session_uuid = str(uuid.uuid4())
        logger.info(
            f"WebSocketManager initialized with session UUID: {self.session_uuid}"
        )

    def _get_stop_cache_key(self, template_id: str, version: str) -> str:
        """Generate cache key for stop streaming flag"""
        return CacheKeyPatterns.STOP_STREAMING.format(
            template_id=template_id, version=version
        )

    def _get_response_cache_key(
        self, template_id: str, version: str, index: int
    ) -> str:
        """Generate cache key for response data"""
        return CacheKeyPatterns.PROMPT_TEMPLATE_RESPONSE.format(
            template_id=template_id, version=version, index=index
        )

    def _get_active_session_uuids_key(self, template_id: str, version: str) -> str:
        """Generate cache key for active session UUIDs"""
        return CacheKeyPatterns.ACTIVE_SESSION_UUIDS.format(
            template_id=template_id, version=version
        )

    def _get_active_session_uuids(self, template_id: str, version: str) -> list[str]:
        """Get list of active session UUIDs for a template/version"""
        try:
            cache_key = self._get_active_session_uuids_key(template_id, version)
            active_uuids = cache.get(cache_key, [])
            return active_uuids if isinstance(active_uuids, list) else []
        except Exception as e:
            logger.error(
                f"Error getting active session UUIDs: {str(e)} , session UUID: {self.session_uuid}"
            )
            return []

    def _set_active_session_uuids(
        self, template_id: str, version: str, session_uuids: list[str]
    ) -> None:
        """Set list of active session UUIDs for a template/version"""
        try:
            cache_key = self._get_active_session_uuids_key(template_id, version)
            cache.set(cache_key, session_uuids, timeout=self._cache_timeout)
        except Exception as e:
            logger.error(
                f"Error setting active session UUIDs: {str(e)} , session UUID: {self.session_uuid}"
            )

    def _add_active_session_uuid(self, template_id: str, version: str) -> None:
        """Add current session UUID to active list"""
        try:
            active_uuids = self._get_active_session_uuids(template_id, version)
            if self.session_uuid not in active_uuids:
                active_uuids.append(self.session_uuid)
                self._set_active_session_uuids(template_id, version, active_uuids)
                logger.debug(
                    f"Added session UUID {self.session_uuid} to active list for template {template_id}, version {version}"
                )
        except Exception as e:
            logger.error(
                f"Error adding active session UUID: {str(e)} , session UUID: {self.session_uuid}"
            )

    def _remove_active_session_uuid(self, template_id: str, version: str) -> None:
        """Remove current session UUID from active list"""
        try:
            active_uuids = self._get_active_session_uuids(template_id, version)
            if self.session_uuid in active_uuids:
                active_uuids.remove(self.session_uuid)
                self._set_active_session_uuids(template_id, version, active_uuids)
                logger.debug(
                    f"Removed session UUID {self.session_uuid} from active list for template {template_id}, version {version}"
                )
        except Exception as e:
            logger.error(
                f"Error removing active session UUID: {str(e)} , session UUID: {self.session_uuid}"
            )

    def _stop_all_previous_session_uuids(
        self, template_id: str, version: str
    ) -> list[str]:
        """Stop all previous session UUIDs for a template/version and return the stopped UUIDs"""
        try:
            active_uuids = self._get_active_session_uuids(template_id, version)
            stopped_uuids = []

            for session_uuid in active_uuids:
                if session_uuid != self.session_uuid:  # Don't stop current session
                    # Set stop flag for this session UUID
                    session_uuid_key = CacheKeyPatterns.STOP_SESSION_UUID.format(
                        session_uuid=session_uuid
                    )
                    cache.set(session_uuid_key, True, timeout=self._cache_timeout)
                    stopped_uuids.append(session_uuid)
                    logger.info(
                        f"Stopped previous session UUID: {session_uuid} for template {template_id}, version {version}"
                    )

            # Clear the active UUIDs list and add only current session
            self._set_active_session_uuids(template_id, version, [self.session_uuid])

            logger.info(
                f"Stopped {len(stopped_uuids)} previous session UUIDs for template {template_id}, version {version}"
            )
            return stopped_uuids

        except Exception as e:
            logger.error(
                f"Error stopping previous session UUIDs: {str(e)} , session UUID: {self.session_uuid}"
            )
            return []

    def is_streaming_stopped(self, template_id: str, version: str) -> bool:
        """Check if streaming has been stopped for a specific template/version"""
        cache_key = self._get_stop_cache_key(template_id, version)
        session_uuid_key = CacheKeyPatterns.STOP_SESSION_UUID.format(
            session_uuid=self.session_uuid
        )
        return bool(cache.get(cache_key)) or bool(cache.get(session_uuid_key))

    def set_stop_streaming(self, template_id: str, version: str) -> None:
        """Set stop streaming flag for a specific template/version"""
        cache_key = self._get_stop_cache_key(template_id, version)
        cache.set(cache_key, True, timeout=self._cache_timeout)
        cache.set(
            CacheKeyPatterns.STOP_SESSION_UUID.format(session_uuid=self.session_uuid),
            True,
            timeout=self._cache_timeout,
        )
        logger.info(
            f"Stop streaming flag set for template {template_id}, version {version} , session UUID: {self.session_uuid}"
        )

    def clear_stop_streaming(self, template_id: str, version: str) -> None:
        """Clear stop streaming flag for a specific template/version"""
        cache_key = self._get_stop_cache_key(template_id, version)
        cache.delete(cache_key)
        session_uuid_key = CacheKeyPatterns.STOP_SESSION_UUID.format(
            session_uuid=self.session_uuid
        )
        cache.set(session_uuid_key, True, timeout=self._cache_timeout)
        # Note: session_uuid key is NOT cleared - it remains as a permanent stop flag for this session
        logger.info(
            f"Stop streaming flag cleared for template {template_id}, version {version} , session UUID: {self.session_uuid}"
        )

    def send_streaming_message(
        self, template_id: str, version: str, streaming_status: str, **kwargs
    ) -> dict[str, Any]:
        """
        Send a standardized streaming message via WebSocket

        Args:
            template_id: Template ID
            version: Version string
            streaming_status: One of WebSocketStatus constants
            **kwargs: Additional message data
        """
        message = WebSocketPayload.create_streaming_payload(
            message_type=WebSocketMessageType.RUN_PROMPT,
            streaming_status=streaming_status,
            version=version,
            session_uuid=self.session_uuid,  # Pass session UUID to payload
            **kwargs,
        )
        if self.is_streaming_stopped(template_id, version):
            return {"status": "stopped", "message": "Streaming was stopped"}
        try:
            result = call_websocket(
                self.organization_id, message, send_to_uuid=True, uuid=str(template_id)
            )
            logger.debug(
                f"WebSocket message sent: {streaming_status} for template {template_id}, version {version}, session UUID: {self.session_uuid}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Failed to send WebSocket message: {str(e)} , session UUID: {self.session_uuid}"
            )
            # Don't raise the exception to prevent streaming from being interrupted
            # Just log the error and continue
            return {"status": "error", "message": str(e)}

    def send_started_message(
        self,
        template_id: str,
        version: str,
        result_index: int,
        num_results: int,
        output_format: str = "string",
    ) -> dict[str, Any]:
        """Send streaming started message"""
        return self.send_streaming_message(
            template_id=template_id,
            version=version,
            streaming_status=WebSocketStatus.STARTED,
            result_index=result_index,
            num_results=num_results,
            output_format=output_format,
        )

    def send_running_message(
        self,
        template_id: str,
        version: str,
        chunk: str,
        chunk_pos: int,
        result_index: int,
        num_results: int,
    ) -> dict[str, Any]:
        """Send streaming running message with chunk data"""
        if self.is_streaming_stopped(template_id, version):
            return {"status": "stopped", "message": "Streaming was stopped"}
        return self.send_streaming_message(
            template_id=template_id,
            version=version,
            streaming_status=WebSocketStatus.RUNNING,
            chunk=chunk,
            chunk_pos=chunk_pos,
            result_index=result_index,
            num_results=num_results,
        )

    def send_completed_message(
        self,
        template_id: str,
        version: str,
        result_index: int,
        num_results: int,
        metadata: dict | None = None,
        output_format: str = "string",
    ) -> dict[str, Any]:
        """Send streaming completed message"""
        message_data = {
            "result_index": result_index,
            "num_results": num_results,
            "output_format": output_format,
        }
        if metadata:
            message_data["metadata"] = metadata

        return self.send_streaming_message(
            template_id=template_id,
            version=version,
            streaming_status=WebSocketStatus.COMPLETED,
            **message_data,
        )

    def send_error_message(
        self,
        template_id: str,
        version: str,
        error: str,
        result_index: int,
        num_results: int,
        output_format: str = "string",
    ) -> dict[str, Any]:
        """Send streaming error message"""
        if self.is_streaming_stopped(template_id, version):
            return {"status": "stopped", "message": "Streaming was stopped"}
        return self.send_streaming_message(
            template_id=template_id,
            version=version,
            streaming_status=WebSocketStatus.ERROR,
            error=error,
            result_index=result_index,
            num_results=num_results,
            output_format=output_format,
        )

    def send_stopped_message(
        self,
        template_id: str,
        version: str,
        partial_response: str,
        result_index: int,
        num_results: int,
        output_format: str = "string",
    ) -> dict[str, Any]:
        """Send streaming stopped message with partial response"""
        return self.send_streaming_message(
            template_id=template_id,
            version=version,
            streaming_status=WebSocketStatus.STOPPED,
            partial_response=partial_response,
            result_index=result_index,
            num_results=num_results,
            output_format=output_format,
        )

    def send_all_completed_message(
        self, template_id: str, version: str
    ) -> dict[str, Any]:
        """Send all streaming completed message"""
        return self.send_streaming_message(
            template_id=template_id,
            version=version,
            streaming_status=WebSocketStatus.ALL_COMPLETED,
        )

    def handle_stop_streaming_request(
        self, template_id: str, versions: list[str], session_uuids: list[str]
    ) -> dict[str, Any]:
        """
        Handle stop streaming request for multiple versions

        Args:
            template_id: Template ID
            versions: List of version strings to stop

        Returns:
            Dict with success/error status
        """
        try:
            for session_uuid in session_uuids:
                self.stop_specific_session_uuid(session_uuid)
            stopped_versions = []
            for version in versions:
                self.set_stop_streaming(template_id, version)
                stopped_versions.append(version)

                # Send immediate stop confirmation
                self.send_stopped_message(
                    template_id=template_id,
                    version=version,
                    partial_response="",  # Will be updated with actual partial response
                    result_index=0,
                    num_results=1,
                )

            logger.info(
                f"Stop streaming requested for template {template_id}, versions: {stopped_versions}, session UUID: {self.session_uuid}"
            )
            return {
                "status": "success",
                "message": f"Version(s) {', '.join(stopped_versions)} has been stopped successfully.",
                "stopped_versions": stopped_versions,
            }

        except Exception as e:
            logger.error(
                f"Error handling stop streaming request: {str(e)} , session UUID: {self.session_uuid}"
            )
            return {
                "status": "error",
                "message": f"Failed to stop streaming: {str(e)}",
            }

    def cleanup_streaming_data(self, template_id: str, version: str) -> None:
        """Clean up all streaming-related cache data"""
        try:
            # Clear stop streaming flag
            self.clear_stop_streaming(template_id, version)

            # Remove current session UUID from active list
            self._remove_active_session_uuid(template_id, version)

            logger.debug(
                f"Cleaned up streaming data for template {template_id}, version {version}, session UUID: {self.session_uuid}"
            )
        except Exception as e:
            logger.error(
                f"Error cleaning up streaming data: {str(e)} , session UUID: {self.session_uuid}"
            )

    def cleanup_streaming_data_for_indices(
        self, template_id: str, version: str, max_index: int
    ) -> None:
        """Clean up streaming cache data for multiple indices"""
        try:
            # # Clear stop streaming flag
            # self.clear_stop_streaming(template_id, version)

            # Clear cached data for each index
            for i in range(max_index):
                cache_key = self._get_response_cache_key(template_id, version, i)
                cache.delete(cache_key)

            logger.debug(
                f"Cleaned up streaming data for template {template_id}, version {version}, indices 0-{max_index - 1}, session UUID: {self.session_uuid}"
            )
        except Exception as e:
            logger.error(
                f"Error cleaning up streaming data for indices: {str(e)} , session UUID: {self.session_uuid}"
            )

    def get_cached_response(
        self, template_id: str, version: str, index: int
    ) -> dict[str, Any] | None:
        """Get cached response for a specific template/version/index"""
        try:
            cache_key = self._get_response_cache_key(template_id, version, index)
            return cache.get(cache_key)
        except Exception as e:
            logger.error(
                f"Error getting cached response: {str(e)} , session UUID: {self.session_uuid}"
            )
            return None

    def set_cached_response(
        self, template_id: str, version: str, index: int, response_data: dict[str, Any]
    ) -> None:
        """Set cached response for a specific template/version/index"""
        try:
            cache_key = self._get_response_cache_key(template_id, version, index)
            cache.set(cache_key, response_data, timeout=self._cache_timeout)
        except Exception as e:
            logger.error(
                f"Error setting cached response: {str(e)} , session UUID: {self.session_uuid}"
            )

    def get_session_uuid(self) -> str:
        """Get the session UUID for this WebSocket manager instance"""
        return self.session_uuid

    def get_active_session_uuids(self, template_id: str, version: str) -> list[str]:
        """Get list of active session UUIDs for a template/version (for debugging)"""
        return self._get_active_session_uuids(template_id, version)

    def stop_specific_session_uuid(self, session_uuid: str) -> bool:
        """
        Stop a specific session UUID (useful for external control)

        Args:
            session_uuid: The session UUID to stop

        Returns:
            True if session was stopped, False otherwise
        """
        try:
            session_uuid_key = CacheKeyPatterns.STOP_SESSION_UUID.format(
                session_uuid=session_uuid
            )
            cache.set(session_uuid_key, True, timeout=60 * 60)
            logger.info(f"Manually stopped session UUID: {session_uuid}")
            return True
        except Exception as e:
            logger.error(
                f"Error stopping specific session UUID {session_uuid}: {str(e)}"
            )
            return False

    def notify_process_started(
        self,
        template_id: str,
        version: str,
        execution_id: str | None = None,
        output_format: str = "string",
        **kwargs,
    ) -> dict[str, Any]:
        """
        Notify UI that a process has started and all inputs will be associated with this session UUID.
        This method also stops all previous session UUIDs for the same template/version.

        Args:
            template_id: Template ID
            version: Version string
            execution_id: Optional execution ID for tracking
            output_format: Output format (string, audio, image)
            **kwargs: Additional context information

        Returns:
            Dict with success/error status and information about stopped sessions
        """
        try:
            # Stop all previous session UUIDs for this template/version
            stopped_uuids = self._stop_all_previous_session_uuids(template_id, version)

            # Clear the general stop streaming flag for this template/version
            cache_key = self._get_stop_cache_key(template_id, version)
            cache.delete(cache_key)

            # Add current session UUID to active list
            self._add_active_session_uuid(template_id, version)

            message = {
                "type": WebSocketMessageType.RUN_PROMPT,
                "session_uuid": self.session_uuid,
                "template_id": template_id,
                "version": version,
                "status": WebSocketStatus.PROCESS_STARTED,
                "timestamp": time.time(),
                "streaming_status": WebSocketStatus.STARTED,
                "output_format": output_format,
            }

            # Add optional execution_id if provided
            if execution_id:
                message["execution_id"] = execution_id

            # Add any additional context
            message.update(kwargs)

            result = call_websocket(
                self.organization_id, message, send_to_uuid=True, uuid=str(template_id)
            )

            logger.info(
                f"Process started notification sent: session UUID {self.session_uuid} for template {template_id}, version {version}"
            )

            logger.info(
                f"Process started notification sent: session UUID {self.session_uuid} for template {template_id}, version {version}. Stopped {len(stopped_uuids)} previous sessions."
            )
            return {
                "status": "success",
                "result": result,
                "stopped_previous_sessions": len(stopped_uuids) > 0,
                "stopped_session_count": len(stopped_uuids),
                "stopped_session_uuids": stopped_uuids,
            }

        except Exception as e:
            logger.error(
                f"Failed to send process started notification: {str(e)} , session UUID: {self.session_uuid}"
            )
            return {"status": "error", "message": str(e)}


# Global WebSocket manager instance factory
def get_websocket_manager(organization_id: str) -> WebSocketManager:
    """Get WebSocket manager instance for an organization"""
    return WebSocketManager(str(organization_id))
