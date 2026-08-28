"""
Utility classes for handlers.

This module contains reusable utilities:
- PayloadBuilder: Clean payload construction
- ModelConfig: Centralized model configuration and feature detection
- ResponseFormatter: Output formatting for all response types
- AudioProcessor: Audio processing utilities for TTS/STT
"""

from agentic_eval.core_evals.run_prompt.runprompt_handlers.utils.model_config import (
    REASONING_MODELS,
    TEMPERATURE_RESTRICTED_MODELS,
    get_model_features,
    is_reasoning_model,
    is_temperature_restricted,
    strip_provider_prefix,
)
from agentic_eval.core_evals.run_prompt.runprompt_handlers.utils.payload_builder import (
    PayloadBuilder,
)
from agentic_eval.core_evals.run_prompt.runprompt_handlers.utils.response_formatter import (
    ResponseFormatter,
    UsageInfo,
)
from agentic_eval.core_evals.run_prompt.runprompt_handlers.utils.audio_processor import (
    AudioProcessor,
    ALLOWED_STT_FORMATS,
    AUDIO_TOKENS_PER_SECOND,
    MAX_TTS_TEXT_LENGTH,
)
from agentic_eval.core_evals.run_prompt.runprompt_handlers.utils.adapters import (
    RunPromptAdapter,
)


__all__ = [
    # Model configuration
    "REASONING_MODELS",
    "TEMPERATURE_RESTRICTED_MODELS",
    "get_model_features",
    "is_reasoning_model",
    "is_temperature_restricted",
    "strip_provider_prefix",
    # Payload building
    "PayloadBuilder",
    # Response formatting
    "ResponseFormatter",
    "UsageInfo",
    # Audio processing
    "AudioProcessor",
    "ALLOWED_STT_FORMATS",
    "AUDIO_TOKENS_PER_SECOND",
    "MAX_TTS_TEXT_LENGTH",
    # Adapters
    "RunPromptAdapter",
]
