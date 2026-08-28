"""
Shared validation utilities for MCP AI tools.

Provides reusable validators that align with UI and backend validation rules
for use as Pydantic field_validators in tool input models.
"""

import re

VALID_AGENT_TYPES = ["voice", "text"]
VALID_PROVIDERS = ["vapi", "retell", "others"]
VALID_AUTH_METHODS = ["api_key", "basicAuth", "bearerToken", "noAuth"]


def validate_agent_type(value: str) -> str:
    """Validate agent_type is 'voice' or 'text'."""
    if value not in VALID_AGENT_TYPES:
        raise ValueError(f"agent_type must be one of: {', '.join(VALID_AGENT_TYPES)}")
    return value


def get_valid_language_codes() -> list[str]:
    """Get valid language codes from the AgentDefinition model."""
    from simulate.models.agent_definition import AgentDefinition

    return [choice[0] for choice in AgentDefinition.LanguageChoices.choices]


def validate_languages(languages: list[str]) -> list[str]:
    """Validate each language code in the list against LanguageChoices."""
    valid = get_valid_language_codes()
    for lang in languages:
        if lang not in valid:
            raise ValueError(
                f"Invalid language '{lang}'. Must be one of: {', '.join(valid)}"
            )
    return languages


def validate_provider(value: str) -> str:
    """Validate provider is one of the supported choices."""
    if value not in VALID_PROVIDERS:
        raise ValueError(f"provider must be one of: {', '.join(VALID_PROVIDERS)}")
    return value


def validate_authentication_method(value: str) -> str:
    """Validate authentication_method is one of the supported choices."""
    if value not in VALID_AUTH_METHODS:
        raise ValueError(
            f"authentication_method must be one of: {', '.join(VALID_AUTH_METHODS)}"
        )
    return value


def validate_contact_number(value: str) -> str:
    """
    Validate contact number format.
    Allows optional '+' prefix, digits only, 10-12 digit length.
    """
    if not value:
        return value
    cleaned = re.sub(r"[^\d]", "", value.lstrip("+"))
    if not re.match(r"^\+?\d+$", value):
        raise ValueError(
            "Contact number must contain only digits (optionally prefixed with +)"
        )
    if len(cleaned) < 10 or len(cleaned) > 12:
        raise ValueError("Contact number must be between 10 and 12 digits")
    return value
