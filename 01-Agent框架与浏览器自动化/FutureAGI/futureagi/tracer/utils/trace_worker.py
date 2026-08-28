import hashlib
import json

from tfc.celery import NUM_TRACE_QUEUES


def get_routing_key(request_data):
    """
    Determines the routing key based on the trace_id to ensure
    spans for the same trace go to the same worker.
    """
    try:
        if isinstance(request_data, str):
            request_data = json.loads(request_data)

        resource_spans = request_data.get("resource_spans", [])
        if not resource_spans:
            return 0, "trace.0"

        first_span = resource_spans[0]["scope_spans"][0]["spans"][0]
        trace_id = first_span.get("trace_id", "default")

        hash_object = hashlib.sha256(trace_id.encode())
        hash_digest = hash_object.hexdigest()
        queue_index = int(hash_digest, 16) % NUM_TRACE_QUEUES
        return queue_index, f"trace.{queue_index}"
    except (IndexError, KeyError, json.JSONDecodeError):
        return 0, "trace.0"
