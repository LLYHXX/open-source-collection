from datetime import UTC, datetime, timedelta

from tracer.utils.otel import (
    CallAttributes,
    ConversationAttributes,
    MessageAttributes,
    SpanAttributes,
)


def normalize_eleven_labs_data(log: dict) -> dict:
    """
    Normalizes a single log entry from ElevenLabs.
    """
    status_map = {"done": "ok", "failed": "error"}
    status = status_map.get(log.get("status", ""), "unset")

    eval_attributes = _extract_eval_attributes(log)
    start_time, end_time = _extract_timestamps(log)
    transcript = log.get("transcript")

    prompt_tokens = eval_attributes.get(SpanAttributes.USAGE_INPUT_TOKENS)
    completion_tokens = eval_attributes.get(SpanAttributes.USAGE_OUTPUT_TOKENS)
    total_tokens = eval_attributes.get(SpanAttributes.USAGE_TOTAL_TOKENS)

    return {
        "id": log.get("conversation_id"),
        "start_time": start_time,
        "end_time": end_time,
        "cost": log.get("metadata", {}).get("cost"),
        "status": status,
        "input": {"transcript": transcript} if transcript else {},
        "metadata": log.get("metadata"),
        "span_attributes": eval_attributes,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def _extract_eval_attributes(log: dict) -> dict:
    """
    Extracts and flattens evaluation attributes from an ElevenLabs log.
    """
    eval_attributes = {
        SpanAttributes.SPAN_KIND: "conversation",
        "raw_log": log,
    }
    _extract_llm_details(log, eval_attributes)
    _extract_transcript(log, eval_attributes)
    _extract_common_call_fields(log, eval_attributes)
    return eval_attributes


def _extract_llm_details(log: dict, eval_attributes: dict):
    """
    Extracts LLM details (model name, token counts) and adds them to eval_attributes.
    """
    llm_usage = log.get("metadata", {}).get("charging", {}).get("llm_usage", {})
    if not llm_usage:
        return

    model_usage = llm_usage.get("initiated_generation", {}).get("model_usage", {})
    model_name = next(iter(model_usage.keys()), None)
    if not model_name:
        return

    eval_attributes[SpanAttributes.REQUEST_MODEL] = model_name
    prompt_tokens = model_usage[model_name].get("input", {}).get("tokens", 0)
    completion_tokens = model_usage[model_name].get("output_total", {}).get("tokens", 0)

    eval_attributes[SpanAttributes.USAGE_INPUT_TOKENS] = prompt_tokens
    eval_attributes[SpanAttributes.USAGE_OUTPUT_TOKENS] = completion_tokens
    eval_attributes[SpanAttributes.USAGE_TOTAL_TOKENS] = (
        prompt_tokens + completion_tokens
    )


def _extract_transcript(log: dict, eval_attributes: dict):
    """
    Extracts and flattens the transcript into the eval_attributes.
    """
    transcript = log.get("transcript")
    if not (transcript and isinstance(transcript, list)):
        return

    for i, msg in enumerate(transcript):
        if msg.get("role"):
            eval_attributes[
                f"{ConversationAttributes.CONVERSATION_TRANSCRIPT}.{i}.{MessageAttributes.MESSAGE_ROLE}"
            ] = msg["role"]
        if msg.get("message"):
            eval_attributes[
                f"{ConversationAttributes.CONVERSATION_TRANSCRIPT}.{i}.{MessageAttributes.MESSAGE_CONTENT}"
            ] = msg["message"]


def _extract_timestamps(log: dict) -> tuple:
    """
    Extracts start and end timestamps from an ElevenLabs log.
    """
    start_time = None
    if start_time_unix := log.get("metadata", {}).get("start_time_unix_secs"):
        start_time = datetime.fromtimestamp(start_time_unix, tz=UTC)

    end_time = None
    if start_time and (duration := log.get("metadata", {}).get("call_duration_secs")):
        end_time = start_time + timedelta(seconds=duration)

    return start_time, end_time


def _extract_common_call_fields(log: dict, eval_attributes: dict):
    """Extracts provider-agnostic call fields into eval_attributes."""
    # total_number_of_turns
    transcript = log.get("transcript", [])
    if isinstance(transcript, list):
        eval_attributes[CallAttributes.TOTAL_TURNS] = sum(
            1 for msg in transcript if msg.get("role") in ("user", "agent")
        )
    else:
        eval_attributes[CallAttributes.TOTAL_TURNS] = 0

    # total_call_duration (seconds, int) — matches duration_seconds in API response
    metadata = log.get("metadata", {}) or {}
    raw_duration = metadata.get("call_duration_secs")
    eval_attributes[CallAttributes.DURATION] = (
        int(raw_duration) if raw_duration is not None else None
    )

    # participant_phone_number (ElevenLabs typically does not provide phone numbers)
    eval_attributes[CallAttributes.PARTICIPANT_PHONE_NUMBER] = None

    # call_status (raw provider status)
    eval_attributes[CallAttributes.STATUS] = log.get("status")

    # wpm and talk_ratio (ElevenLabs does not provide per-message timing data)
    eval_attributes[CallAttributes.USER_WPM] = None
    eval_attributes[CallAttributes.BOT_WPM] = None
    eval_attributes[CallAttributes.TALK_RATIO] = None
