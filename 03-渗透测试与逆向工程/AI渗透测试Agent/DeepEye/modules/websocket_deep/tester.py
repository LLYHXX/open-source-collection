"""WebSocket deep: CSWSH, origin bypass, message injection heuristics."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from utils.logger import get_logger

logger = get_logger(__name__)


class WebSocketDeepTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("websocket_deep") or {}

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        context = context or {}
        vulns: List[Dict] = []
        candidates = self._candidates(url, context)
        for ws_http in candidates:
            vulns.extend(self._probe_upgrade(ws_http, url))
            vulns.extend(self._probe_origin(ws_http))
            vulns.extend(self._probe_injection_headers(ws_http))
        return vulns

    def _candidates(self, url: str, context: Dict) -> List[str]:
        out = set()
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        paths = ["/ws", "/websocket", "/socket", "/socket.io/", "/api/ws", "/realtime"]
        for p in paths:
            out.add(urljoin(base + "/", p.lstrip("/")))
        # from page content
        body = ""
        if context.get("response") is not None:
            body = getattr(context["response"], "text", "") or ""
        for token in ("wss://", "ws://"):
            if token in body:
                # crude extract
                idx = body.find(token)
                frag = body[idx : idx + 120]
                end = min(
                    (frag.find(c) for c in " \"'<>" if frag.find(c) > 0),
                    default=len(frag),
                )
                cand = frag[:end]
                if cand.startswith("ws"):
                    # convert to http for upgrade probe
                    out.add(cand.replace("wss://", "https://").replace("ws://", "http://"))
        if "ws" in url.lower() or "socket" in url.lower():
            out.add(url.replace("wss://", "https://").replace("ws://", "http://"))
        return list(out)[:8]

    def _probe_upgrade(self, http_url: str, origin_url: str) -> List[Dict]:
        try:
            resp = self.http_client.get(
                http_url,
                headers={
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                    "Sec-WebSocket-Version": "13",
                    "Origin": "https://evil.example",
                },
            )
            if not resp:
                return []
            st = getattr(resp, "status_code", 0)
            h = {k.lower(): str(v) for k, v in dict(getattr(resp, "headers", {}) or {}).items()}
            if st == 101 or "websocket" in str(h.get("upgrade", "")).lower():
                return [{
                    "type": "WebSocket Endpoint Exposed",
                    "severity": "medium",
                    "url": http_url,
                    "parameter": "Upgrade",
                    "payload": "websocket",
                    "evidence": f"HTTP {st} upgrade={h.get('upgrade')}",
                    "description": "WebSocket upgrade accepted; test auth/origin separately",
                    "remediation": "Require authentication and strict Origin checks on WS handshake",
                }]
            if st in (200, 400, 403, 426):
                return [{
                    "type": "WebSocket Handshake Reachable",
                    "severity": "info",
                    "url": http_url,
                    "parameter": "Upgrade",
                    "payload": "websocket",
                    "evidence": f"HTTP {st} on WS upgrade probe",
                    "description": "Server responds to WebSocket upgrade requests",
                    "remediation": "Ensure WS endpoints enforce auth and origin policy",
                }]
        except Exception as e:
            logger.debug(f"ws upgrade: {e}")
        return []

    def _probe_origin(self, http_url: str) -> List[Dict]:
        findings = []
        for origin in ("https://evil.example", "null", "https://attacker.com"):
            try:
                resp = self.http_client.get(
                    http_url,
                    headers={
                        "Upgrade": "websocket",
                        "Connection": "Upgrade",
                        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                        "Sec-WebSocket-Version": "13",
                        "Origin": origin,
                    },
                )
                if not resp:
                    continue
                st = getattr(resp, "status_code", 0)
                if st == 101:
                    findings.append({
                        "type": "WebSocket Cross-Site (CSWSH) Origin Accepted",
                        "severity": "high",
                        "url": http_url,
                        "parameter": "Origin",
                        "payload": origin,
                        "evidence": f"Upgrade 101 with Origin={origin}",
                        "description": "WebSocket accepts untrusted Origin (CSWSH risk)",
                        "remediation": "Whitelist Origin values; bind session to origin",
                    })
                    break
            except Exception as e:
                logger.debug(f"ws origin: {e}")
        return findings

    def _probe_injection_headers(self, http_url: str) -> List[Dict]:
        payload = "'; DROP TABLE users;--"
        try:
            resp = self.http_client.get(
                http_url,
                headers={
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                    "Sec-WebSocket-Version": "13",
                    "Sec-WebSocket-Protocol": payload,
                    "X-WS-Payload": f"<script>alert(1)</script>",
                },
            )
            if not resp:
                return []
            body = (getattr(resp, "text", "") or "")[:2000]
            if payload in body or "<script>" in body:
                return [{
                    "type": "WebSocket Handshake Injection Reflection",
                    "severity": "medium",
                    "url": http_url,
                    "parameter": "Sec-WebSocket-Protocol",
                    "payload": payload,
                    "evidence": "Handshake header payload reflected in response",
                    "description": "Untrusted WS handshake fields reflected — validate strictly",
                    "remediation": "Do not reflect Sec-WebSocket-* values into HTML/logs without encoding",
                }]
        except Exception as e:
            logger.debug(f"ws inject: {e}")
        return []
