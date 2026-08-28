import time
from typing import Any, Dict

import structlog
from channels.db import database_sync_to_async
from django.core.cache import cache

logger = structlog.get_logger(__name__)


class WebSocketDirectManager:
    def __init__(
        self,
        organization_id: int,
        channel_name: str,
        session_uuid: str,
        channel_layer: Any,
        consumer_send_json_func: callable = None,
    ):
        self.organization_id = organization_id
        self.channel_name = channel_name
        self.session_uuid = session_uuid
        self.channel_layer = channel_layer
        self.consumer_send_json_func = consumer_send_json_func
        logger.info(
            f"WebSocketDirectManager initialized: channel={self.channel_name}, session={self.session_uuid}"
        )

    async def _send_to_channel(self, data: Dict[str, Any]):
        if self.consumer_send_json_func:
            try:
                await self.consumer_send_json_func(data)
            except Exception as e:
                logger.warning(
                    f"Failed to send to consumer (connection likely closed): {e}"
                )
            return

        try:
            await self.channel_layer.send(
                self.channel_name, {"type": "stream_message", "data": data}
            )
        except Exception as e:
            logger.error(f"Failed to send to channel layer: {e}")

    async def notify_process_started(
        self,
        template_id: str,
        version: str,
        execution_id: str,
        process_type: str,
        total_iterations: int,
        output_format: str = "string",
    ):
        message = {
            "type": "run_prompt",
            "session_uuid": self.session_uuid,
            "template_id": template_id,
            "version": version,
            "status": "process_started",
            "streaming_status": "started",
            "timestamp": time.time(),
            "execution_id": execution_id,
            "process_type": process_type,
            "total_iterations": total_iterations,
            "output_format": output_format,
        }
        await self._send_to_channel(message)

    async def send_started_message(
        self,
        template_id: str,
        version: str,
        result_index: int,
        num_results: int,
        output_format: str = "string",
    ):
        message = {
            "type": "run_prompt",
            "streaming_status": "started",
            "template_id": template_id,
            "version": version,
            "session_uuid": self.session_uuid,
            "result_index": result_index,
            "num_results": num_results,
            "output_format": output_format,
        }
        await self._send_to_channel(message)

    async def send_running_message(
        self,
        template_id: str,
        version: str,
        chunk: str,
        chunk_pos: int,
        result_index: int,
        num_results: int,
    ):
        message = {
            "type": "run_prompt",
            "streaming_status": "running",
            "template_id": template_id,
            "version": version,
            "session_uuid": self.session_uuid,
            "chunk": chunk,
            "chunk_pos": chunk_pos,
            "result_index": result_index,
            "num_results": num_results,
        }
        await self._send_to_channel(message)

    async def send_completed_message(
        self,
        template_id: str,
        version: str,
        result_index: int,
        num_results: int,
        metadata: dict,
        output_format: str = "string",
    ):
        message = {
            "type": "run_prompt",
            "streaming_status": "completed",
            "template_id": template_id,
            "version": version,
            "session_uuid": self.session_uuid,
            "result_index": result_index,
            "num_results": num_results,
            "metadata": metadata,
            "output_format": output_format,
        }
        await self._send_to_channel(message)

    async def send_all_completed_message(self, template_id: str, version: str):
        message = {
            "type": "run_prompt",
            "streaming_status": "all_completed",
            "template_id": template_id,
            "version": version,
            "session_uuid": self.session_uuid,
        }
        await self._send_to_channel(message)

    async def send_error_message(
        self,
        template_id: str,
        version: str,
        error: str,
        result_index: int,
        num_results: int,
        output_format: str = "string",
    ):
        message = {
            "type": "run_prompt",
            "streaming_status": "error",
            "template_id": template_id,
            "version": version,
            "session_uuid": self.session_uuid,
            "error": error,
            "result_index": result_index,
            "num_results": num_results,
            "output_format": output_format,
        }
        await self._send_to_channel(message)

    async def send_stopped_message(
        self,
        template_id: str,
        version: str,
        partial_response: str,
        result_index: int,
        num_results: int,
        output_format: str = "string",
    ):
        message = {
            "type": "run_prompt",
            "streaming_status": "stopped",
            "template_id": template_id,
            "version": version,
            "session_uuid": self.session_uuid,
            "partial_response": partial_response,
            "result_index": result_index,
            "num_results": num_results,
            "output_format": output_format,
        }
        await self._send_to_channel(message)

    @database_sync_to_async
    def is_streaming_stopped(self, template_id: str, version: str):
        key = f"streaming_status_{self.organization_id}_{template_id}_{version}"
        return cache.get(key) == "stopped"

    @database_sync_to_async
    def set_stop_streaming(self, template_id: str, version: str):
        """Set stop streaming flag for a specific template/version"""
        key = f"streaming_status_{self.organization_id}_{template_id}_{version}"
        cache.set(key, "stopped", timeout=60)
        logger.info(
            f"Stop streaming flag set for template {template_id}, version {version}, session UUID: {self.session_uuid}"
        )

    @database_sync_to_async
    def set_cached_response(
        self, template_id: str, version: str, index: int, response_data: dict[str, Any]
    ):
        key = (
            f"streaming_response_{self.organization_id}_{template_id}_{version}_{index}"
        )
        cache.set(key, response_data, timeout=60 * 5)

    @database_sync_to_async
    def cleanup_streaming_data(self, template_id: str, version: str):
        status_key = f"streaming_status_{self.organization_id}_{template_id}_{version}"
        cache.delete(status_key)

    @database_sync_to_async
    def cleanup_streaming_data_for_indices(self, template_id, version, max_len):
        for i in range(max_len):
            key = (
                f"streaming_response_{self.organization_id}_{template_id}_{version}_{i}"
            )
            cache.delete(key)

    # Methods for improve_prompt
    async def send_improve_prompt_activity_message(
        self,
        improve_id: str,
        current_activity: str,
        status: str = "running",
        chunk: str = "",
        chunk_pos: int = 0,
    ):
        """Send activity update message for improve_prompt"""
        message = {
            "type": "improve_prompt",
            "improve_id": improve_id,
            "current_activity": current_activity,
            "status": status,
            "session_uuid": self.session_uuid,
            "chunk": chunk,
            "chunk_pos": chunk_pos,
        }
        await self._send_to_channel(message)

    async def send_improve_prompt_completed_message(self, improve_id: str, prompt: str):
        """Send completion message for improve_prompt"""
        message = {
            "type": "improve_prompt",
            "improve_id": improve_id,
            "status": "completed",
            "prompt": prompt,
            "session_uuid": self.session_uuid,
        }
        await self._send_to_channel(message)

    async def send_improve_prompt_error_message(self, improve_id: str, error: str):
        """Send error message for improve_prompt"""
        message = {
            "type": "improve_prompt",
            "improve_id": improve_id,
            "status": "error",
            "error": error,
            "session_uuid": self.session_uuid,
        }
        await self._send_to_channel(message)

    @database_sync_to_async
    def is_improve_prompt_stopped(self, improve_id: str):
        """Check if improve_prompt streaming is stopped"""
        key = f"improve_prompt_status_{self.organization_id}_{improve_id}"
        return cache.get(key) == "stopped"

    @database_sync_to_async
    def set_stop_improve_prompt(self, improve_id: str):
        """Set stop flag for improve_prompt"""
        key = f"improve_prompt_status_{self.organization_id}_{improve_id}"
        cache.set(key, "stopped", timeout=60)
        logger.info(
            f"Stop improve_prompt flag set for improve_id {improve_id}, session UUID: {self.session_uuid}"
        )

    # Methods for generate_prompt
    async def send_generate_prompt_activity_message(
        self,
        generation_id: str,
        current_activity: str,
        status: str = "running",
        chunk: str = "",
        chunk_pos: int = 0,
    ):
        """Send activity update message for generate_prompt"""
        message = {
            "type": "generate_prompt",
            "generation_id": generation_id,
            "current_activity": current_activity,
            "status": status,
            "session_uuid": self.session_uuid,
            "chunk": chunk,
            "chunk_pos": chunk_pos,
        }
        await self._send_to_channel(message)

    async def send_generate_prompt_completed_message(
        self, generation_id: str, prompt: str
    ):
        """Send completion message for generate_prompt"""
        message = {
            "type": "generate_prompt",
            "generation_id": generation_id,
            "status": "completed",
            "prompt": prompt,
            "session_uuid": self.session_uuid,
        }
        await self._send_to_channel(message)

    async def send_generate_prompt_error_message(self, generation_id: str, error: str):
        """Send error message for generate_prompt"""
        message = {
            "type": "generate_prompt",
            "generation_id": generation_id,
            "status": "error",
            "error": error,
            "session_uuid": self.session_uuid,
        }
        await self._send_to_channel(message)

    @database_sync_to_async
    def is_generate_prompt_stopped(self, generation_id: str):
        """Check if generate_prompt streaming is stopped"""
        key = f"generate_prompt_status_{self.organization_id}_{generation_id}"
        return cache.get(key) == "stopped"

    @database_sync_to_async
    def set_stop_generate_prompt(self, generation_id: str):
        """Set stop flag for generate_prompt"""
        key = f"generate_prompt_status_{self.organization_id}_{generation_id}"
        cache.set(key, "stopped", timeout=60)
        logger.info(
            f"Stop generate_prompt flag set for generation_id {generation_id}, session UUID: {self.session_uuid}"
        )
