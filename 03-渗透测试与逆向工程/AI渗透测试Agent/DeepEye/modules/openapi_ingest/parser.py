"""OpenAPI 3 / Swagger 2 → URL + parameter inventory."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

from utils.logger import get_logger

logger = get_logger(__name__)


def load_openapi(source: str, http_client=None) -> Optional[Dict]:
    """Load OpenAPI from path or URL."""
    try:
        if source.startswith("http://") or source.startswith("https://"):
            if not http_client:
                return None
            resp = http_client.get(source)
            if not resp or not getattr(resp, "text", None):
                return None
            text = resp.text
        else:
            text = Path(source).read_text(encoding="utf-8")
        if source.endswith((".yaml", ".yml")) or text.lstrip().startswith(("openapi:", "swagger:")):
            try:
                import yaml
                return yaml.safe_load(text)
            except Exception:
                pass
        return json.loads(text)
    except Exception as e:
        logger.warning(f"OpenAPI load failed: {e}")
        return None


def expand_endpoints(spec: Dict, base_url: str = "") -> List[Dict]:
    """
    Expand paths to concrete endpoint dicts:
      {url, method, parameters: [{name, in, required}], tags}
    """
    if not spec:
        return []
    servers = spec.get("servers") or []
    if servers and not base_url:
        base_url = str(servers[0].get("url", "")).rstrip("/")
    base_url = (base_url or "").rstrip("/")

    # Swagger 2 host/basePath
    if not base_url and spec.get("host"):
        scheme = (spec.get("schemes") or ["https"])[0]
        base_url = f"{scheme}://{spec['host']}{spec.get('basePath', '')}".rstrip("/")

    out: List[Dict] = []
    paths = spec.get("paths") or {}
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.lower() not in (
                "get", "post", "put", "patch", "delete", "head", "options"
            ):
                continue
            if not isinstance(op, dict):
                continue
            params = list(op.get("parameters") or [])
            # path-level params
            params.extend(methods.get("parameters") or [])
            concrete = path
            for p in params:
                if not isinstance(p, dict):
                    continue
                if p.get("in") == "path":
                    name = p.get("name", "id")
                    sample = _sample_for_schema(p.get("schema") or p)
                    concrete = concrete.replace("{" + name + "}", str(sample))
            url = urljoin(base_url + "/", concrete.lstrip("/")) if base_url else concrete
            out.append(
                {
                    "url": url,
                    "method": method.upper(),
                    "parameters": [
                        {
                            "name": p.get("name"),
                            "in": p.get("in"),
                            "required": bool(p.get("required")),
                        }
                        for p in params
                        if isinstance(p, dict) and p.get("name")
                    ],
                    "tags": op.get("tags") or [],
                    "operation_id": op.get("operationId") or "",
                }
            )
    logger.info(f"OpenAPI expanded {len(out)} endpoints")
    return out


def _sample_for_schema(schema: Dict) -> str:
    if not isinstance(schema, dict):
        return "1"
    t = schema.get("type") or schema.get("schema", {}).get("type")
    if t == "integer" or t == "number":
        return "1"
    if t == "boolean":
        return "true"
    fmt = schema.get("format") or ""
    if fmt == "uuid":
        return "00000000-0000-0000-0000-000000000001"
    return "test"
