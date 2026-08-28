import json


def parse_image_urls(value: str) -> list[str]:
    """Parse image URLs from a JSON array or comma-separated string.

    Supports two formats:
    1. JSON array: '["url1", "url2"]'
    2. Comma-separated: 'url1, url2'

    Returns a list of stripped, non-empty URL strings.
    """
    value = value.strip()
    if value.startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list) and all(
                isinstance(item, str) for item in parsed
            ):
                return [p.strip() for p in parsed if p.strip()]
        except (json.JSONDecodeError, TypeError):
            pass
    return [url.strip() for url in value.split(",") if url.strip()]
