"""Detect third-party JS libs + missing SRI + common vuln versions."""
from __future__ import annotations

import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

from utils.logger import get_logger

logger = get_logger(__name__)

_SCRIPT_RE = re.compile(
    r"<script[^>]+src=[\"']([^\"']+)[\"']([^>]*)>",
    re.I,
)

_VULN_LIBS = [
    (re.compile(r"jquery[_-]?(1\.[0-9]|2\.[0-2]|3\.[0-4])", re.I), "jQuery <3.5 known XSS issues"),
    (re.compile(r"angular[_-]?1\.[0-8]", re.I), "AngularJS 1.x EOL / sandbox escapes"),
    (re.compile(r"lodash[_-]?(3\.|4\.[0-16]\.)", re.I), "lodash prototype pollution era"),
    (re.compile(r"moment[_-]?2\.(0|1[0-9]|2[0-9])\.", re.I), "old moment.js"),
    (re.compile(r"bootstrap[_-]?(3\.|4\.[0-5])", re.I), "old Bootstrap XSS/tooltip issues"),
    (re.compile(r"handlebars[_-]?(3\.|4\.[0-6])", re.I), "Handlebars prototype pollution era"),
    (re.compile(r"vue[@/]2\.[0-5]", re.I), "Vue 2 early versions"),
    (re.compile(r"react[_-]?1[0-5]\.", re.I), "very old React"),
    (re.compile(r"dompurify[_-]?1\.", re.I), "DOMPurify 1.x"),
    (re.compile(r"prototype\.js", re.I), "Prototype.js legacy"),
]


class SupplyChainJSTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        html = ""
        if context and context.get("response") is not None:
            html = getattr(context["response"], "text", "") or ""
        if not html:
            resp = self.http_client.get(url)
            html = getattr(resp, "text", "") or "" if resp else ""
        if not html:
            return []
        vulns: List[Dict] = []
        page_host = (urlparse(url).netloc or "").lower()
        for m in _SCRIPT_RE.finditer(html):
            src = m.group(1)
            attrs = m.group(2) or ""
            if src.startswith("//"):
                src = "https:" + src
            parsed = urlparse(src if "://" in src else urljoin_safe(url, src))
            host = (parsed.netloc or "").lower()
            if host and host != page_host and "integrity=" not in attrs.lower():
                vulns.append({
                    "type": "Third-party Script Missing SRI",
                    "severity": "medium",
                    "url": url,
                    "parameter": "script.src",
                    "payload": src,
                    "evidence": src[:200],
                    "description": "Cross-origin script without Subresource Integrity",
                    "remediation": "Add integrity= and crossorigin= on third-party scripts",
                })
            if host and host != page_host and "crossorigin" not in attrs.lower():
                vulns.append({
                    "type": "Third-party Script Missing crossorigin",
                    "severity": "low",
                    "url": url,
                    "parameter": "script.src",
                    "payload": src,
                    "evidence": src[:200],
                    "description": "Cross-origin script without crossorigin attribute",
                    "remediation": "Add crossorigin=anonymous with SRI",
                })
            for cre, desc in _VULN_LIBS:
                if cre.search(src):
                    vulns.append({
                        "type": "Outdated JavaScript Library",
                        "severity": "medium",
                        "url": url,
                        "parameter": "script.src",
                        "payload": src,
                        "evidence": desc,
                        "description": f"Potentially vulnerable library: {desc}",
                        "remediation": "Upgrade library; pin versions; enable SRI",
                    })
        seen = set()
        uniq = []
        for v in vulns:
            k = (v["type"], v.get("payload"))
            if k in seen:
                continue
            seen.add(k)
            uniq.append(v)
        return uniq


def urljoin_safe(base: str, rel: str) -> str:
    from urllib.parse import urljoin
    return urljoin(base, rel)
