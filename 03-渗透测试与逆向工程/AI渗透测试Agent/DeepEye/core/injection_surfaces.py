"""Multi-surface parameter discovery + injection dispatch."""
from __future__ import annotations

import json
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


class Surface(str, Enum):
    QUERY = "query"
    FORM_POST = "form_post"
    JSON_BODY = "json_body"
    COOKIE = "cookie"
    HEADER = "header"
    PATH_SEGMENT = "path_segment"


Param = Tuple[str, str]  # name, default value


def extract_surfaces(url: str, context: Optional[Dict] = None) -> Dict[Surface, List[Param]]:
    """Discover injectable parameters across surfaces."""
    context = context or {}
    out: Dict[Surface, List[Param]] = {s: [] for s in Surface}

    parsed = urlparse(url or "")
    qs = parse_qs(parsed.query, keep_blank_values=True)
    for k, vals in qs.items():
        out[Surface.QUERY].append((k, vals[0] if vals else ""))
    stub = context.get("openapi_query_stub") or ""
    if stub and isinstance(stub, str):
        for k, vals in parse_qs(stub, keep_blank_values=True).items():
            out[Surface.QUERY].append((k, vals[0] if vals else ""))
    for name in context.get("query_params") or []:
        out[Surface.QUERY].append((str(name), ""))

    for form in context.get("forms") or []:
        if not isinstance(form, dict):
            continue
        method = str(form.get("method") or "GET").upper()
        if method == "GET":
            for inp in form.get("inputs") or []:
                name = (inp or {}).get("name") or ""
                if name:
                    out[Surface.QUERY].append((name, str((inp or {}).get("value") or "")))
        else:
            for inp in form.get("inputs") or []:
                name = (inp or {}).get("name") or ""
                if name:
                    out[Surface.FORM_POST].append(
                        (name, str((inp or {}).get("value") or ""))
                    )

    # JSON body hints from OpenAPI or prior context
    for name in context.get("json_params") or []:
        out[Surface.JSON_BODY].append((str(name), ""))
    body = context.get("json_body")
    if isinstance(body, dict):
        for k, v in body.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                out[Surface.JSON_BODY].append((str(k), "" if v is None else str(v)))

    cookies = context.get("cookies") or {}
    if isinstance(cookies, dict):
        for k, v in cookies.items():
            out[Surface.COOKIE].append((str(k), str(v)))

    headers = context.get("injectable_headers") or [
        "X-Forwarded-For",
        "X-Original-URL",
        "X-Rewrite-URL",
        "Referer",
        "User-Agent",
    ]
    for h in headers:
        out[Surface.HEADER].append((str(h), ""))

    # numeric / uuid-like path segments
    for seg in (parsed.path or "").split("/"):
        if not seg:
            continue
        if re.fullmatch(r"\d{1,12}", seg) or re.fullmatch(
            r"[0-9a-fA-F-]{8,36}", seg
        ):
            out[Surface.PATH_SEGMENT].append((seg, seg))

    # de-dupe per surface
    for s in list(out.keys()):
        seen = set()
        uniq = []
        for name, val in out[s]:
            key = (name, val)
            if key in seen:
                continue
            seen.add(key)
            uniq.append((name, val))
        out[s] = uniq
    return out


def inject(
    url: str,
    context: Optional[Dict],
    surface: Surface,
    param: str,
    value: str,
    http_client=None,
    method: str = "GET",
):
    """Build and send request with payload on the given surface. Returns response or None."""
    context = context or {}
    if http_client is None:
        raise ValueError("http_client required")

    parsed = urlparse(url)

    if surface == Surface.QUERY:
        qs = parse_qs(parsed.query, keep_blank_values=True)
        qs[param] = [value]
        test_url = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
        return http_client.get(test_url)

    if surface == Surface.FORM_POST:
        # merge form defaults if present
        data = {}
        for form in context.get("forms") or []:
            if str(form.get("method") or "").upper() in ("POST", "PUT", "PATCH"):
                for inp in form.get("inputs") or []:
                    n = (inp or {}).get("name")
                    if n:
                        data[n] = (inp or {}).get("value") or ""
        data[param] = value
        action = url
        for form in context.get("forms") or []:
            if form.get("action"):
                from urllib.parse import urljoin
                action = urljoin(url, form["action"])
                break
        return http_client.post(action, data=data)

    if surface == Surface.JSON_BODY:
        body = dict(context.get("json_body") or {})
        body[param] = value
        return http_client.post(
            url,
            json=body,
            headers={"Content-Type": "application/json"},
        )

    if surface == Surface.COOKIE:
        return http_client.get(url, headers={"Cookie": f"{param}={value}"})

    if surface == Surface.HEADER:
        return http_client.get(url, headers={param: value})

    if surface == Surface.PATH_SEGMENT:
        # replace first occurrence of param segment
        parts = (parsed.path or "/").split("/")
        for i, seg in enumerate(parts):
            if seg == param:
                parts[i] = value
                break
        else:
            # append if not found
            parts.append(value)
        new_path = "/".join(parts)
        if not new_path.startswith("/"):
            new_path = "/" + new_path
        test_url = urlunparse(parsed._replace(path=new_path))
        return http_client.get(test_url)

    return None


def surfaces_for_injection_checks(
    url: str, context: Optional[Dict] = None
) -> List[Tuple[Surface, str, str]]:
    """Flat list of (surface, name, default) for iteration in _check_* methods."""
    flat = []
    for surface, params in extract_surfaces(url, context).items():
        if surface in (Surface.HEADER,) and not (context or {}).get("probe_headers"):
            # headers are expensive; only when explicitly requested or for dedicated modules
            continue
        for name, default in params:
            flat.append((surface, name, default))
    # always include query even if empty? no — short-circuit if nothing
    return flat
