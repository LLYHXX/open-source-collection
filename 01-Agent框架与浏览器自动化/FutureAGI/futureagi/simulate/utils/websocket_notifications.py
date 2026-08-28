import json
import threading

import redis
import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)

_redis_client = None
_redis_lock = threading.Lock()


def _get_redis():
    global _redis_client
    if _redis_client is None:
        with _redis_lock:
            if _redis_client is None:
                _redis_client = redis.from_url(
                    settings.REDIS_URL,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
    return _redis_client


def notify_simulation_update(organization_id, run_test_id, test_execution_id=None):
    """
    Publish a simulation update notification via Redis pub/sub.

    The SimulationUpdateConsumer subscribes to the organization-scoped channel
    and forwards the message to the connected frontend client over WebSocket.
    """
    channel = f"simulation_updates:{organization_id}:{run_test_id}"
    message = json.dumps(
        {
            "type": "simulation_update",
            "data": {
                "run_test_id": str(run_test_id),
                "test_execution_id": (
                    str(test_execution_id) if test_execution_id else None
                ),
            },
        }
    )
    try:
        _get_redis().publish(channel, message)
        logger.info(
            "simulation_update_published",
            run_test_id=str(run_test_id),
            test_execution_id=str(test_execution_id) if test_execution_id else None,
        )
    except Exception:
        logger.exception(
            "Failed to publish simulation_update to Redis",
            run_test_id=str(run_test_id),
        )
