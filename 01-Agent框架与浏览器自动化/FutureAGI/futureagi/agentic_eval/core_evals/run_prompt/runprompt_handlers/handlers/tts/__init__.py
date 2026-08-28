"""
TTS sub-handlers.

This module contains specialized handlers for different TTS paths:
- SpeechAPIHandler: Standard TTS via litellm.speech()
- AudioPreviewHandler: OpenAI audio-preview models (gpt-4o-audio-preview)
- CustomTTSHandler: ElevenLabs, Cartesia, Deepgram, etc.
"""

from .audio_preview_handler import AudioPreviewHandler
from .custom_tts_handler import CustomTTSHandler
from .speech_api_handler import SpeechAPIHandler

__all__ = [
    "AudioPreviewHandler",
    "CustomTTSHandler",
    "SpeechAPIHandler",
]
