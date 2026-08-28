from __future__ import annotations

import logging
from typing import Dict
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)


def _get_query_param(url: str, key: str) -> str | None:
    if not url:
        return None
    try:
        return parse_qs(urlparse(url).query).get(key, [None])[0]
    except (ValueError, TypeError, KeyError, IndexError):
        return None


def _is_v1_endpoint(api_base: str) -> bool:
    if not api_base:
        return False
    return "/openai/v1" in api_base.lower()


def _infer_endpoint_type(api_base: str) -> str:
    if not api_base:
        return "foundry"
    base = api_base.lower()
    if ".openai.azure.com" in base or "/openai/deployments/" in base:
        return "legacy"
    if (
        ".services.ai.azure.com" in base
        or ".models.ai.azure.com" in base
        or ".inference.ai.azure.com" in base
        or ".cognitiveservices.azure.com" in base
    ):
        return "foundry"
    logger.warning(
        "Could not infer Azure endpoint type from URL '%s', defaulting to 'foundry'",
        api_base,
    )
    return "foundry"


def _strip_legacy_base(api_base: str) -> str:
    if not api_base:
        return api_base
    parsed = urlparse(api_base)
    if not parsed.scheme:
        # Try adding https:// and re-parsing
        parsed = urlparse(f"https://{api_base}")
    return f"{parsed.scheme}://{parsed.netloc}"


# Path prefixes that must be preserved for foundry endpoints
_FOUNDRY_KEEP_PATHS = ("/anthropic", "/api/projects/")


def _strip_foundry_base(api_base: str) -> str:
    if not api_base:
        return api_base
    parsed = urlparse(api_base)
    if not parsed.scheme:
        # Try adding https:// and re-parsing
        parsed = urlparse(f"https://{api_base}")
    path = parsed.path.rstrip("/")
    for prefix in _FOUNDRY_KEEP_PATHS:
        idx = path.find(prefix)
        if idx != -1:
            return f"{parsed.scheme}://{parsed.netloc}{path[idx:]}"
    return f"{parsed.scheme}://{parsed.netloc}"


def normalize_azure_custom_model_config(config_json: Dict) -> Dict:
    api_base = config_json.get("api_base") or config_json.get("apiBase")
    api_key = config_json.get("api_key") or config_json.get("apiKey")
    api_version = config_json.get("api_version") or config_json.get("apiVersion")

    endpoint_type = config_json.get("azure_endpoint_type") or config_json.get(
        "azureEndpointType"
    )
    if not endpoint_type:
        endpoint_type = _infer_endpoint_type(api_base)

    is_v1 = _is_v1_endpoint(api_base)

    if not api_version:
        if is_v1:
            api_version = "v1"
        else:
            api_version = _get_query_param(api_base, "api-version")

    if endpoint_type == "legacy":
        api_base = _strip_legacy_base(api_base)
    else:
        api_base = _strip_foundry_base(api_base)

    normalized = {
        "api_base": api_base,
        "api_version": api_version,
        "api_key": api_key,
        "azure_endpoint_type": endpoint_type,
    }

    return normalized
