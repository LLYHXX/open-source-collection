import time
import uuid
from typing import Any

import structlog
from django.core.cache import cache

logger = structlog.get_logger(__name__)


class SyntheticTaskManager:
    """
    Manages synthetic dataset generation tasks using Django cache for coordination.
    Focuses on task cancellation when update requests come in.
    Only the latest request for a dataset continues processing.
    """

    def __init__(self):
        self.task_prefix = "synthetic_task"
        self.cancel_prefix = "synthetic_cancel"
        self.latest_prefix = "synthetic_latest"
        self.regenerate_prefix = "synthetic_regenerate"

    def _get_task_key(self, dataset_id: str) -> str:
        """Generate cache key for task tracking"""
        return f"{self.task_prefix}:{dataset_id}"

    def _get_cancel_key(self, dataset_id: str) -> str:
        """Generate cache key for cancellation flag"""
        return f"{self.cancel_prefix}:{dataset_id}"

    def _get_latest_key(self, dataset_id: str) -> str:
        """Generate cache key for latest task UUID"""
        return f"{self.latest_prefix}:{dataset_id}"

    def _get_regenerate_key(self, dataset_id: str) -> str:
        """Generate cache key for latest task UUID"""
        return f"{self.regenerate_prefix}:{dataset_id}"

    def operation_regenerate_key(self, dataset_id: str, op="add"):
        """
        Add, remove, or check regenerate key for a dataset.

        Args:
            dataset_id: The dataset ID
            op: Operation type - "add" to set regenerate flag, "remove" to delete it, "get" to check if set

        Returns:
            bool: True if operation successful (for add/remove), or True/False if regenerate flag is set (for get)
        """
        try:
            regenerate_key = self._get_regenerate_key(dataset_id)

            if op == "add":
                # Set regenerate flag with 24 hour expiration
                cache.set(regenerate_key, "1", timeout=86400)
                logger.info(f"Added regenerate flag for dataset {dataset_id}")
                return True
            elif op == "remove":
                # Remove regenerate flag
                cache.delete(regenerate_key)
                logger.info(f"Removed regenerate flag for dataset {dataset_id}")
                return True
            elif op == "get":
                # Check if regenerate flag is set
                is_set = cache.get(regenerate_key) is not None
                logger.info(
                    f"Regenerate flag for dataset {dataset_id} is {'set' if is_set else 'not set'}"
                )
                return is_set
            else:
                logger.error(
                    f"Invalid operation '{op}' for regenerate key. Use 'add', 'remove', or 'get'"
                )
                return False

        except Exception as e:
            logger.error(
                f"Failed to {op} regenerate key for dataset {dataset_id}: {str(e)}"
            )
            return False

    def start_task(self, dataset_id: str) -> str:
        """
        Start tracking a new synthetic dataset generation task.
        Generates a unique UUID for this request and cancels any previous ones.

        Args:
            dataset_id: The dataset ID
            task_id: The Celery task ID

        Returns:
            str: The unique UUID for this request
        """
        try:
            # Generate unique UUID for this request
            request_uuid = str(uuid.uuid4())
            task_key = self._get_task_key(dataset_id)
            cancel_key = self._get_cancel_key(dataset_id)
            latest_key = self._get_latest_key(dataset_id)

            # Store task information with UUID
            task_info = {
                "task_id": request_uuid,
                "dataset_id": dataset_id,
                "request_uuid": request_uuid,
                "status": "running",
                "started_at": str(int(time.time())),
            }

            # Get the previous latest UUID if it exists
            previous_latest = cache.get(latest_key)

            # Set new task as latest
            cache.set(latest_key, request_uuid, timeout=86400)  # 24 hours

            # Store task info with expiration (24 hours)
            cache.set(task_key, task_info, timeout=86400)  # 24 hours

            # If there was a previous request, cancel it
            if previous_latest and previous_latest != request_uuid:
                # Set cancellation flag for the previous request
                cache.set(
                    f"{cancel_key}:{previous_latest}", "1", timeout=3600 * 3
                )  # 1 hour expiration
                logger.info(
                    f"Cancelled previous request {previous_latest} for dataset {dataset_id}"
                )

            logger.info(
                f"Started synthetic task tracking for dataset {dataset_id} with UUID {request_uuid}"
            )
            return request_uuid

        except Exception as e:
            logger.error(
                f"Failed to start task tracking for dataset {dataset_id}: {str(e)}"
            )
            return None

    def stop_task(self, dataset_id: str, request_uuid: str) -> bool:
        """
        Stop a specific synthetic dataset generation task by UUID.

        Args:
            dataset_id: The dataset ID
            request_uuid: The specific request UUID to stop

        Returns:
            bool: True if task stopped successfully
        """
        try:
            cancel_key = f"{self._get_cancel_key(dataset_id)}:{request_uuid}"

            # Set cancellation flag for this specific request
            cache.set(cancel_key, "1", timeout=3600)  # 1 hour expiration

            logger.info(
                f"Set cancellation flag for dataset {dataset_id} request {request_uuid}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to stop task for dataset {dataset_id} request {request_uuid}: {str(e)}"
            )
            return False

    def is_cancelled(self, dataset_id: str, request_uuid: str) -> bool:
        """
        Check if a specific task has been cancelled.

        Args:
            dataset_id: The dataset ID
            request_uuid: The specific request UUID to check

        Returns:
            bool: True if task is cancelled
        """
        try:
            cancel_key = f"{self._get_cancel_key(dataset_id)}:{request_uuid}"
            return cache.get(cancel_key) is not None

        except Exception as e:
            logger.error(
                f"Failed to check cancellation status for dataset {dataset_id} request {request_uuid}: {str(e)}"
            )
            return False

    def is_latest_request(self, dataset_id: str, request_uuid: str) -> bool:
        """
        Check if this request is the latest one for the dataset.

        Args:
            dataset_id: The dataset ID
            request_uuid: The request UUID to check

        Returns:
            bool: True if this is the latest request
        """
        try:
            latest_key = self._get_latest_key(dataset_id)
            latest_uuid = cache.get(latest_key)
            return latest_uuid == request_uuid

        except Exception as e:
            logger.error(
                f"Failed to check if request {request_uuid} is latest for dataset {dataset_id}: {str(e)}"
            )
            return False

    def update_progress(
        self, dataset_id: str, request_uuid: str, percentage: float
    ) -> bool:
        """
        Update the progress percentage for a specific task.

        Args:
            dataset_id: The dataset ID
            request_uuid: The request UUID
            percentage: The percentage of completion (0.0 to 100.0)

        Returns:
            bool: True if progress updated successfully
        """
        try:
            task_key = self._get_task_key(dataset_id)
            task_data = cache.get(task_key)

            if not task_data:
                logger.warning(f"No task data found for dataset {dataset_id}")
                return False

            # Check if this is the correct request
            if task_data.get("request_uuid") != request_uuid:
                logger.warning(f"Request UUID mismatch for dataset {dataset_id}")
                return False

            # Update the progress
            task_data["progress"] = percentage
            task_data["last_updated"] = str(int(time.time()))

            # Store updated task info
            cache.set(task_key, task_data, timeout=86400)  # 24 hours

            logger.info(
                f"Updated progress for dataset {dataset_id} request {request_uuid}: {percentage:.1f}%"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to update progress for dataset {dataset_id} request {request_uuid}: {str(e)}"
            )
            return False

    def get_progress(self, dataset_id: str, request_uuid: None) -> float | None:
        """
        Get the current progress percentage for a specific task.

        Args:
            dataset_id: The dataset ID
            request_uuid: The request UUID

        Returns:
            Optional[float]: The progress percentage or None if not found
        """
        try:
            task_key = self._get_task_key(dataset_id)
            task_data = cache.get(task_key)

            if not task_data:
                return 100.0

            return task_data.get("progress", 0.0)

        except Exception as e:
            logger.error(
                f"Failed to get progress for dataset {dataset_id} request {request_uuid}: {str(e)}"
            )
            return 100.0

    def get_task_info(self, dataset_id: str) -> dict[str, Any] | None:
        """
        Get current task information.

        Args:
            dataset_id: The dataset ID

        Returns:
            Optional[Dict]: Task information or None if not found
        """
        try:
            task_key = self._get_task_key(dataset_id)
            task_data = cache.get(task_key)

            if task_data:
                return task_data
            return None

        except Exception as e:
            logger.error(f"Failed to get task info for dataset {dataset_id}: {str(e)}")
            return None

    def clear_task_data(self, dataset_id: str) -> bool:
        """
        Clear all cache data for a dataset.

        Args:
            dataset_id: The dataset ID

        Returns:
            bool: True if data cleared successfully
        """
        try:
            task_key = self._get_task_key(dataset_id)
            self._get_cancel_key(dataset_id)
            latest_key = self._get_latest_key(dataset_id)

            # Get all keys to delete
            keys_to_delete = [task_key, latest_key]

            # Delete all keys
            for key in keys_to_delete:
                cache.delete(key)

            # Delete all cancellation flags for this dataset
            # Note: We can't easily enumerate all keys, so we'll let them expire naturally

            logger.info(f"Cleared task data for dataset {dataset_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to clear task data for dataset {dataset_id}: {str(e)}"
            )
            return False
