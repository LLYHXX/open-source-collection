"""Server-Sent Events (SSE) endpoint discovery + injection heuristics."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)


class SSEInjectionTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("sse_injection") or {}

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        context = context or {}
        vulns: List[Dict] = []
        for sse_url in self._candidates(url, context):
            vulns.extend(self._probe(sse_url))
        # inject into query if present
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        if qs:
            for key in list(qs.keys())[:3]:
                for payload in ("data: <script>alert(1)</script>\n\n", "event: error\ndata: x\n\n", "retry:0\ndata:x\n\n"):
                    try:
                        qs2 = {k: list(v) for k, v in qs.items()}
                        qs2[key] = [payload]
                        test = urlunparse(parsed._replace(query=urlencode(qs2, doseq=True)))
                        resp = self.http_client.get(
                            test,
                            headers={"Accept": "text/event-stream"},
                        )
                        if not resp:
                            continue
                        body = getattr(resp, "text", "") or ""
                        ct = str(dict(getattr(resp, "headers", {}) or {}).get("Content-Type", ""))
                        if "text/event-stream" in ct.lower() or body.startswith("data:"):
                            if payload.strip() in body or "<script>" in body:
                                vulns.append({
                                    "type": "SSE Injection / Reflection",
                                    "severity": "medium",
                                    "url": test,
                                    "parameter": key,
                                    "payload": payload[:80],
                                    "evidence": f"Content-Type={ct}; body snippet reflected",
                                    "description": "SSE stream reflects attacker-controlled event data",
                                    "remediation": "Encode SSE data fields; never embed raw HTML/JS in events",
                                })
                                break
                    except Exception as e:
                        logger.debug(f"sse inject: {e}")
        return vulns

    def _candidates(self, url: str, context: Dict) -> List[str]:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        paths = ["/events", "/sse", "/stream", "/api/events", "/api/stream", "/notifications/stream"]
        out = [urljoin(base + "/", p.lstrip("/")) for p in paths]
        body = ""
        if context.get("response") is not None:
            body = getattr(context["response"], "text", "") or ""
        if "text/event-stream" in body or "EventSource" in body:
            out.append(url)
        return list(dict.fromkeys(out))[:8]

    def _probe(self, sse_url: str) -> List[Dict]:
        try:
            resp = self.http_client.get(
                sse_url,
                headers={"Accept": "text/event-stream", "Cache-Control": "no-cache"},
            )
            if not resp:
                return []
            headers = {k.lower(): str(v) for k, v in dict(getattr(resp, "headers", {}) or {}).items()}
            ct = headers.get("content-type", "")
            body = (getattr(resp, "text", "") or "")[:500]
            st = getattr(resp, "status_code", 0)
            if "text/event-stream" in ct.lower() or body.startswith("data:") or "event:" in body[:100]:
                finding = {
                    "type": "SSE Endpoint Detected",
                    "severity": "info",
                    "url": sse_url,
                    "parameter": "Accept",
                    "payload": "text/event-stream",
                    "evidence": f"HTTP {st} Content-Type={ct}",
                    "description": "Server-Sent Events stream endpoint reachable",
                    "remediation": "Authenticate SSE; rate-limit; validate event payloads",
                }
                # missing auth heuristic
                if st == 200 and not headers.get("www-authenticate"):
                    finding["severity"] = "low"
                    finding["type"] = "SSE Endpoint Possibly Unauthenticated"
                    finding["description"] = "SSE stream returned 200 without WWW-Authenticate"
                return [finding]
        except Exception as e:
            logger.debug(f"sse probe: {e}")
        return []
