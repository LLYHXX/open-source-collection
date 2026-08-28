"""
Audio content handling utilities for LLM multimodal messages.

This module provides utilities to detect and preprocess audio content in
LLM messages for different providers (OpenAI, Vertex AI, Azure, Anthropic).

The issue being solved (CORE-BACKEND-YR0):
Audio content was being sent with type "image_url" which caused errors like
"Unsupported image format: mp3" when providers (especially Anthropic fallback)
tried to process it as an image.

Solution:
1. Audio agents now use "audio_content" type for audio data
2. This module preprocesses messages to convert to provider-specific formats
3. Fallback logic can skip non-audio-supporting providers
"""

from typing import Any, Dict, List
import copy
import structlog

from agentic_eval.core.utils.functions import (
    download_audio_to_base64 as _download_audio_to_base64,
)

logger = structlog.get_logger(__name__)

# Type aliases
Messages = List[Dict[str, Any]]

# Audio MIME types that we support
AUDIO_MIME_TYPES = frozenset(
    [
        "audio/mp3",
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
        "audio/flac",
        "audio/aac",
        "audio/m4a",
        "audio/webm",
    ]
)

# Audio file extensions
AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".webm", ".mpeg")


def _get_audio_format_from_url(url: str) -> str:
    """
    Extract audio format from URL extension.

    Args:
        url: The URL to check

    Returns:
        Audio format string (e.g., "mp3", "wav") or "mp3" as default
    """
    lower_url = url.lower()
    for ext in AUDIO_EXTENSIONS:
        if lower_url.endswith(ext):
            return ext[1:]  # Remove the leading dot
    return "mp3"  # Default


def download_audio_url_to_base64(url: str) -> tuple[str, str]:
    """
    Download audio from a URL and convert to base64.

    Uses the existing download_audio_to_base64 function and infers format from URL.

    Args:
        url: The URL to download audio from

    Returns:
        Tuple of (base64_data, format) where format is like "mp3", "wav", etc.

    Raises:
        Exception: If the audio cannot be downloaded
    """
    audio_format = _get_audio_format_from_url(url)
    base64_data = _download_audio_to_base64(url)
    return base64_data, audio_format


def is_audio_url(url: str) -> bool:
    """
    Check if a URL contains audio content based on data URL prefix or file extension.

    Args:
        url: The URL to check (can be a data URL or file URL)

    Returns:
        True if the URL contains/references audio content
    """
    if not url:
        return False

    # Check data URL prefix
    if url.startswith("data:audio/"):
        return True

    # Check file extensions
    lower_url = url.lower()
    return any(lower_url.endswith(ext) for ext in AUDIO_EXTENSIONS)


def messages_contain_audio(messages: Messages) -> bool:
    """
    Check if any message contains audio content.

    Checks for:
    - audio_content type (our new format)
    - input_audio type (OpenAI format)
    - image_url with audio data URL (legacy incorrect usage)

    Args:
        messages: List of message dictionaries

    Returns:
        True if any message contains audio content
    """
    if not messages:
        return False

    for message in messages:
        content = message.get("content")
        if not content:
            continue

        # Handle list of content blocks
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue

                block_type = block.get("type", "")

                # Check for audio_content type (our format)
                if block_type == "audio_content":
                    return True

                # Check for input_audio type (OpenAI format)
                if block_type == "input_audio":
                    return True

                # Check for image_url that's actually audio (legacy incorrect usage)
                if block_type == "image_url":
                    image_data = block.get("image_url", {})
                    if isinstance(image_data, dict):
                        url = image_data.get("url", "")
                        if is_audio_url(url):
                            return True

    return False


def preprocess_messages_for_provider(messages: Messages, provider: str) -> Messages:
    """
    Preprocess messages to convert audio_content to provider-specific format.

    Different providers expect audio in different formats:
    - vertex_ai: Uses image_url with audio data URL
    - openai/azure: Uses input_audio type
    - anthropic: Does not support audio - strips audio blocks
    - others: Strips audio blocks (safest default)

    Args:
        messages: List of message dictionaries
        provider: The LLM provider name (e.g., "openai", "vertex_ai", "anthropic")

    Returns:
        New list of messages with audio content converted for the provider
    """
    if not messages:
        return messages

    provider_lower = provider.lower() if provider else ""

    # Deep copy to avoid modifying original
    result = copy.deepcopy(messages)

    for message in result:
        content = message.get("content")
        if not content or not isinstance(content, list):
            continue

        new_content = []
        for block in content:
            if not isinstance(block, dict):
                new_content.append(block)
                continue

            block_type = block.get("type", "")

            if block_type == "audio_content":
                # Convert audio_content to provider-specific format
                audio_data = block.get("audio_content", {})
                if isinstance(audio_data, dict):
                    url = audio_data.get("url", "")
                    audio_format = audio_data.get("format", "mp3")

                    if "vertex" in provider_lower:
                        # Vertex AI: Use image_url (it handles audio through this)
                        new_content.append(
                            {"type": "image_url", "image_url": {"url": url}}
                        )
                    elif "openai" in provider_lower or "azure" in provider_lower:
                        # OpenAI/Azure: Use input_audio type
                        # Extract base64 data if it's a data URL
                        if url.startswith("data:audio/"):
                            # Parse data URL: data:audio/mp3;base64,<data>
                            try:
                                header, data = url.split(",", 1)
                                # Extract format from header if possible
                                if "audio/" in header:
                                    fmt_part = header.split("audio/")[1].split(";")[0]
                                    if fmt_part:
                                        audio_format = fmt_part
                            except ValueError:
                                data = url

                            new_content.append(
                                {
                                    "type": "input_audio",
                                    "input_audio": {
                                        "data": data,
                                        "format": audio_format,
                                    },
                                }
                            )
                        else:
                            # Not a data URL - download and convert to base64
                            # This fixes the "Unsupported image format: mp3" error
                            try:
                                data, audio_format = download_audio_url_to_base64(url)
                                new_content.append(
                                    {
                                        "type": "input_audio",
                                        "input_audio": {
                                            "data": data,
                                            "format": audio_format,
                                        },
                                    }
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to download audio URL for OpenAI/Azure, skipping: {e}"
                                )
                                # Skip this audio block since we can't process it
                                pass
                    else:
                        # Other providers (including anthropic): Skip audio
                        # Anthropic doesn't support audio, so we skip it
                        # to prevent errors
                        pass
                else:
                    # Invalid audio_content format, skip
                    pass
            else:
                # Keep non-audio blocks as-is
                new_content.append(block)

        message["content"] = new_content

    return result
