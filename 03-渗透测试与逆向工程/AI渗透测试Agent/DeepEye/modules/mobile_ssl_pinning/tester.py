"""Detect SSL pinning indicators in mobile packages + suggest Frida bypass."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

_PIN_PATTERNS = [
    (re.compile(rb"CertificatePinner|OkHttpClient\.Builder\(\).*certificatePinner", re.I), "OkHttp CertificatePinner"),
    (re.compile(rb"TrustManagerImpl|X509TrustManager|checkServerTrusted", re.I), "Custom TrustManager"),
    (re.compile(rb"Network Security Config|network_security_config|pin-set", re.I), "Android Network Security Config pins"),
    (re.compile(rb"SSLPeerUnverifiedException", re.I), "SSLPeerUnverifiedException usage"),
    (re.compile(rb"SecTrustEvaluate|NSURLSession.*didReceiveChallenge", re.I), "iOS trust evaluation hooks"),
    (re.compile(rb"Public-Key-Pins|sha256/[A-Za-z0-9+/=]{40,}", re.I), "Public key pin material"),
]


class MobileSSLPinningTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("mobile_ssl_pinning") or self.config.get("mobile") or {}

    def scan(self, url: str = "", context: Optional[Dict] = None) -> List[Dict]:
        context = context or {}
        artifact = context.get("artifact") or self.cfg.get("artifact") or ""
        if not artifact:
            return []
        path = Path(artifact)
        if not path.exists():
            return []

        blob = b""
        try:
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path, "r") as zf:
                    for name in zf.namelist():
                        if name.endswith((".dex", ".xml", ".js", ".json", "Info.plist")):
                            try:
                                blob += zf.read(name)[:400_000]
                            except Exception:
                                pass
                        if len(blob) > 3_000_000:
                            break
            else:
                blob = path.read_bytes()[:2_000_000]
        except Exception as e:
            logger.debug(f"pinning scan read: {e}")
            return []

        findings = []
        for cre, label in _PIN_PATTERNS:
            if cre.search(blob):
                findings.append({
                    "type": "Mobile SSL Pinning Indicator",
                    "severity": "info",
                    "url": url or str(path),
                    "parameter": "ssl_pinning",
                    "payload": label,
                    "evidence": f"Pattern matched: {label}",
                    "description": (
                        "App appears to implement certificate/public-key pinning. "
                        "Dynamic analysis may require Frida SSL bypass scripts "
                        "(modules/frida_mobile)."
                    ),
                    "remediation": "Pinning is good for production; ensure pins rotate and backup pins exist",
                    "frida_hint": "ssl_pinning_android / ssl_pinning_ios",
                })
        return findings
