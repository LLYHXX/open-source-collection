"""CORS + CSP misconfiguration checks."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import urlparse

from utils.logger import get_logger

logger = get_logger(__name__)


class CorsCspTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []
        vulns.extend(self._cors(url))
        vulns.extend(self._preflight(url))
        vulns.extend(self._csp(url, context))
        return vulns

    def _cors(self, url: str) -> List[Dict]:
        out = []
        host = urlparse(url).hostname or "target.local"
        origins = [
            "https://evil.example",
            "null",
            f"https://{host}.evil.example",
            f"https://evil.{host}",
            "https://evil.example%60." + host,
        ]
        for origin in origins:
            try:
                resp = self.http_client.get(url, headers={"Origin": origin})
                if not resp:
                    continue
                h = {k.lower(): v for k, v in dict(resp.headers).items()}
                acao = h.get("access-control-allow-origin", "")
                acac = h.get("access-control-allow-credentials", "")
                if acao == "*":
                    sev = "high" if str(acac).lower() == "true" else "medium"
                    out.append({
                        "type": "CORS Wildcard ACAO",
                        "severity": sev,
                        "url": url,
                        "parameter": "Origin",
                        "payload": origin,
                        "evidence": f"ACAO={acao} ACAC={acac}",
                        "description": "Access-Control-Allow-Origin is * (worse with credentials)",
                        "remediation": "Return explicit trusted origins, never * with credentials",
                    })
                elif acao == origin or acao == "null":
                    sev = "high" if str(acac).lower() == "true" else "medium"
                    out.append({
                        "type": "CORS Origin Reflection",
                        "severity": sev,
                        "url": url,
                        "parameter": "Origin",
                        "payload": origin,
                        "evidence": f"ACAO={acao} ACAC={acac}",
                        "description": "Server reflects arbitrary Origin in ACAO",
                        "remediation": "Whitelist allowed origins server-side",
                    })
                    if str(acac).lower() == "true":
                        break
            except Exception as e:
                logger.debug(f"CORS check failed: {e}")
        return out

    def _preflight(self, url: str) -> List[Dict]:
        try:
            origin = "https://evil.example"
            resp = self.http_client.request(
                "OPTIONS",
                url,
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "PUT",
                    "Access-Control-Request-Headers": "X-Custom-Auth, Authorization",
                },
            ) if hasattr(self.http_client, "request") else self.http_client.get(
                url,
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "PUT",
                },
            )
            if not resp:
                return []
            h = {k.lower(): str(v) for k, v in dict(getattr(resp, "headers", {}) or {}).items()}
            acao = h.get("access-control-allow-origin", "")
            acam = h.get("access-control-allow-methods", "")
            acah = h.get("access-control-allow-headers", "")
            if acao in (origin, "*") and (
                "PUT" in acam.upper() or "*" in acam or "authorization" in acah.lower()
            ):
                return [{
                    "type": "CORS Preflight Permissive",
                    "severity": "medium",
                    "url": url,
                    "parameter": "OPTIONS",
                    "payload": origin,
                    "evidence": f"ACAO={acao} ACAM={acam} ACAH={acah}",
                    "description": "Preflight allows untrusted origin with sensitive methods/headers",
                    "remediation": "Restrict ACAO/ACAM/ACAH to required values only",
                }]
        except Exception as e:
            logger.debug(f"CORS preflight: {e}")
        return []

    def _csp(self, url: str, context: Optional[Dict]) -> List[Dict]:
        out = []
        headers = {}
        resp = (context or {}).get("response")
        if resp is not None:
            headers = {k.lower(): v for k, v in dict(getattr(resp, "headers", {}) or {}).items()}
        else:
            r = self.http_client.get(url)
            if r:
                headers = {k.lower(): v for k, v in dict(r.headers).items()}
        csp = headers.get("content-security-policy") or headers.get(
            "content-security-policy-report-only"
        )
        if not csp:
            out.append({
                "type": "Missing Content-Security-Policy",
                "severity": "low",
                "url": url,
                "parameter": "",
                "payload": "",
                "evidence": "No CSP header",
                "description": "Missing CSP increases XSS impact",
                "remediation": "Deploy a strict Content-Security-Policy",
            })
            return out
        csp_l = str(csp).lower()
        if "unsafe-inline" in csp_l:
            out.append({
                "type": "CSP unsafe-inline",
                "severity": "medium",
                "url": url,
                "parameter": "Content-Security-Policy",
                "payload": "",
                "evidence": str(csp)[:300],
                "description": "CSP allows unsafe-inline scripts/styles",
                "remediation": "Remove unsafe-inline; use nonces or hashes",
            })
        if "unsafe-eval" in csp_l:
            out.append({
                "type": "CSP unsafe-eval",
                "severity": "medium",
                "url": url,
                "parameter": "Content-Security-Policy",
                "payload": "",
                "evidence": str(csp)[:300],
                "description": "CSP allows unsafe-eval",
                "remediation": "Remove unsafe-eval from script-src",
            })
        if "script-src *" in csp_l or "script-src*" in csp_l or "default-src *" in csp_l:
            out.append({
                "type": "CSP Wildcard script-src",
                "severity": "medium",
                "url": url,
                "parameter": "Content-Security-Policy",
                "payload": "",
                "evidence": str(csp)[:300],
                "description": "CSP allows wildcard script sources",
                "remediation": "Pin script-src to trusted hosts; avoid *",
            })
        if "data:" in csp_l and "script-src" in csp_l:
            out.append({
                "type": "CSP data: in script-src",
                "severity": "medium",
                "url": url,
                "parameter": "Content-Security-Policy",
                "payload": "",
                "evidence": str(csp)[:300],
                "description": "data: URIs in script-src enable XSS gadgets",
                "remediation": "Remove data: from script-src",
            })
        if "trusted-types" not in csp_l and "require-trusted-types-for" not in csp_l:
            out.append({
                "type": "CSP Missing Trusted Types",
                "severity": "info",
                "url": url,
                "parameter": "Content-Security-Policy",
                "payload": "",
                "evidence": "No Trusted-Types directive",
                "description": "Trusted Types not enforced (DOM XSS mitigation)",
                "remediation": "Add require-trusted-types-for 'script' where supported",
            })
        return out
