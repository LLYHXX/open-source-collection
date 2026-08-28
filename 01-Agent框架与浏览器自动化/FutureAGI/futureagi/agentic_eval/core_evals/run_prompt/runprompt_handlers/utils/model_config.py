"""
Centralized model configuration and feature detection.

This module provides a single source of truth for model-specific behaviors.
Useful for:
- UI hints about model capabilities
- Documentation and introspection
- Feature detection for advanced use cases

NOTE: LiteLLM with drop_params=True handles actual parameter adjustments
automatically for most providers. The model lists here are primarily for
informational purposes rather than runtime parameter manipulation.
"""

from typing import Set

# Reasoning models (o1/o3/o4/gpt-5 series)
# These models have special parameter requirements that LiteLLM handles:
# - max_tokens -> max_completion_tokens conversion
# - Temperature restricted to 1.0 (with drop_params=True)
REASONING_MODELS: Set[str] = {
    # o1 series
    "o1",
    "o1-2024-12-17",
    "o1-mini",
    "o1-mini-2024-09-12",
    "o1-preview",
    "o1-preview-2024-09-12",
    "o1-pro",
    "o1-pro-2025-03-19",
    # o3 series
    "o3",
    "o3-2025-04-16",
    "o3-mini",
    "o3-mini-2025-01-31",
    "o3-pro",
    "o3-pro-2025-06-10",
    # o4 series
    "o4-mini",
    "o4-mini-2025-04-16",
    # GPT-5 series (all are reasoning models)
    "gpt-5",
    "gpt-5-2025-08-07",
    "gpt-5-mini",
    "gpt-5-mini-2025-08-07",
    "gpt-5-nano",
    "gpt-5-nano-2025-08-07",
    "gpt-5-chat-latest",
    "gpt-5-pro",
    "gpt-5-pro-2025-10-06",
    "gpt-5-codex",
    "gpt-5-codex-2025-09-01",
    # GPT-5.1 series
    "gpt-5.1",
    "gpt-5.1-2025-11-13",
    "gpt-5.1-chat-latest",
    "gpt-5.1-codex",
    "gpt-5.1-codex-mini",
    "gpt-5.1-codex-max",
    # GPT-5.2 series
    "gpt-5.2",
    "gpt-5.2-2025-12-11",
    "gpt-5.2-chat-latest",
    "gpt-5.2-pro",
    "gpt-5.2-pro-2025-12-11",
}

# Claude models with temperature restrictions
# These models don't support custom temperature values (only default 1.0)
TEMPERATURE_RESTRICTED_MODELS: Set[str] = {
    "claude-haiku-4-5-20251001",
    "claude-opus-4-1-20250805",
    "claude-opus-4-5-20251001",
    "claude-sonnet-4-5-20250929",
}


def strip_provider_prefix(model: str) -> str:
    """
    Strip provider prefix from model name.

    Handles prefixes like:
    - azure/o3-mini -> o3-mini
    - bedrock/claude-4 -> claude-4
    - openai/gpt-5 -> gpt-5

    Args:
        model: Full model name possibly with provider prefix

    Returns:
        Model name without provider prefix
    """
    if "/" in model:
        return model.split("/")[-1]
    return model


def is_reasoning_model(model: str) -> bool:
    """
    Check if model is a reasoning model (o1/o3/o4/gpt-5 series).

    NOTE: LiteLLM handles parameter adjustments automatically when
    drop_params=True is set. This function is primarily for informational
    purposes (UI hints, documentation, etc.).

    Args:
        model: Model name (with or without provider prefix)

    Returns:
        True if model is a reasoning model
    """
    model_name = strip_provider_prefix(model)
    return model_name in REASONING_MODELS


def is_temperature_restricted(model: str) -> bool:
    """
    Check if model has temperature restrictions (Claude 4+ models).

    NOTE: LiteLLM handles parameter adjustments automatically when
    drop_params=True is set. This function is primarily for informational
    purposes (UI hints, documentation, etc.).

    Args:
        model: Model name (with or without provider prefix)

    Returns:
        True if model is temperature-restricted
    """
    model_name = strip_provider_prefix(model)
    return model_name in TEMPERATURE_RESTRICTED_MODELS


def get_model_features(model: str) -> dict:
    """
    Get all feature flags for a model.

    Useful for UI hints, documentation, and introspection.

    Args:
        model: Model name

    Returns:
        Dict with feature flags:
        - is_reasoning: Bool (model is o1/o3/o4/gpt-5 series)
        - is_temperature_restricted: Bool (model only supports temp=1.0)
        - stripped_name: Model name without provider prefix
        - has_prefix: Bool (original model name had provider prefix)
    """
    stripped = strip_provider_prefix(model)
    return {
        "is_reasoning": stripped in REASONING_MODELS,
        "is_temperature_restricted": stripped in TEMPERATURE_RESTRICTED_MODELS,
        "stripped_name": stripped,
        "has_prefix": "/" in model,
    }
