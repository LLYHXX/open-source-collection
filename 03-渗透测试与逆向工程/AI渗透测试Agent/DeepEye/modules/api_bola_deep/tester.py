"""API BOLA/IDOR deep: role swap, sequential IDs, mass assignment on JSON APIs."""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

_ID_RE = re.compile(r"(?<=[=/])(\d{1,12})(?=/|$|&)")
_API_HINT = re.compile(r"/api/|/v\d+/|/graphql|/rest/|/users/|/accounts/", re.I)


class APIBolaDeepTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("api_bola_deep") or {}
        self.max_probes = int(self.cfg.get("max_probes", 8))

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        context = context or {}
        if not _API_HINT.search(url) and not self.cfg.get("force", False):
            # still run if JSON content-type
            headers = context.get("headers") or {}
            ct = str(headers.get("content-type") or headers.get("Content-Type") or "")
            if "json" not in ct.lower() and "/api" not in url.lower():
                return []

        vulns: List[Dict] = []
        baseline = context.get("response")
        if baseline is None:
            baseline = self.http_client.get(url)
        if not baseline:
            return vulns

        base_status = getattr(baseline, "status_code", 0)
        base_body = getattr(baseline, "text", "") or ""
        base_len = len(base_body)
        if base_status not in (200, 201):
            return vulns

        # sequential ID swaps
        for mut_url, param in self._id_mutations(url)[: self.max_probes]:
            try:
                resp = self.http_client.get(mut_url)
                if not resp:
                    continue
                st = getattr(resp, "status_code", 0)
                body = getattr(resp, "text", "") or ""
                if st == 200 and abs(len(body) - base_len) > 40:
                    # different resource likely
                    if body != base_body:
                        vulns.append({
                            "type": "API BOLA / IDOR",
                            "severity": "high",
                            "url": mut_url,
                            "parameter": param,
                            "payload": mut_url,
                            "evidence": f"status={st} len={len(body)} vs baseline={base_len}",
                            "description": "Object ID change returned different authorized content",
                            "remediation": "Enforce object-level authorization on every API object access",
                        })
            except Exception as e:
                logger.debug(f"api bola: {e}")

        # JSON mass-assignment probe on POST-like endpoints
        if any(x in url.lower() for x in ("/users", "/profile", "/account", "/api/")):
            for body in (
                {"role": "admin", "isAdmin": True, "admin": True},
                {"user_id": 1, "id": 1, "accountId": 0},
            ):
                try:
                    resp = self.http_client.post(
                        url,
                        json=body,
                        headers={"Content-Type": "application/json"},
                    )
                    if not resp:
                        continue
                    text = (getattr(resp, "text", "") or "").lower()
                    st = getattr(resp, "status_code", 0)
                    if st in (200, 201) and any(
                        k in text for k in ("admin", "role", "\"id\":1", "isadmin")
                    ):
                        vulns.append({
                            "type": "API Mass Assignment Probe",
                            "severity": "medium",
                            "url": url,
                            "parameter": "json",
                            "payload": json.dumps(body),
                            "evidence": f"HTTP {st} accepted privileged fields",
                            "description": "API may bind unexpected JSON properties",
                            "remediation": "Use allowlists for deserializable fields; never bind role/admin flags",
                        })
                        break
                except Exception as e:
                    logger.debug(f"mass assign probe: {e}")

        # method confusion GET vs DELETE
        try:
            del_resp = self.http_client.get(
                url, headers={"X-HTTP-Method-Override": "DELETE"}
            )
            if del_resp and getattr(del_resp, "status_code", 0) in (200, 204):
                vulns.append({
                    "type": "API Method Override on Resource",
                    "severity": "medium",
                    "url": url,
                    "parameter": "X-HTTP-Method-Override",
                    "payload": "DELETE",
                    "evidence": f"HTTP {del_resp.status_code}",
                    "description": "Resource accepted method override — verify authorization",
                    "remediation": "Disable method override or authorize each verb independently",
                })
        except Exception:
            pass

        return vulns

    def _id_mutations(self, url: str) -> List[tuple]:
        out = []
        parsed = urlparse(url)
        for m in _ID_RE.finditer(parsed.path):
            n = int(m.group(1))
            for delta in (1, -1, 2, 999, 0):
                nn = max(0, n + delta)
                new_path = parsed.path[: m.start(1)] + str(nn) + parsed.path[m.end(1) :]
                out.append((urlunparse(parsed._replace(path=new_path)), f"path:{m.group(1)}"))
        qs = parse_qs(parsed.query, keep_blank_values=True)
        for key, vals in qs.items():
            if vals and vals[0].isdigit():
                n = int(vals[0])
                for delta in (1, -1, 2):
                    qs2 = {k: list(v) for k, v in qs.items()}
                    qs2[key] = [str(max(0, n + delta))]
                    out.append(
                        (
                            urlunparse(parsed._replace(query=urlencode(qs2, doseq=True))),
                            key,
                        )
                    )
        return out
