import re

SAFE_AGENTCC_NAME_REGEX = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_AGENTCC_NAME_ERROR = (
    "Name can only contain letters, numbers, hyphens, and underscores"
)


def validate_safe_agentcc_name(value: str) -> str:
    cleaned = value.strip()
    if not SAFE_AGENTCC_NAME_REGEX.fullmatch(cleaned):
        raise ValueError(SAFE_AGENTCC_NAME_ERROR)
    return cleaned
