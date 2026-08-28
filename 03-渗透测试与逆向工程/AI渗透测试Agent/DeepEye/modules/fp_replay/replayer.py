"""False-positive replay: re-probe findings marked FP with alternate payloads."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

_ALTS = {
    "xss": ["\"'><svg/onload=1>", "{{7*7}}", "<img src=x onerror=alert(1)>"],
    "sql": ["' OR '1'='1'--", "1) AND 1=1--", "SLEEP(0)"],
    "default": ["'\"<>", "{{7*7}}", "${7*7}"],
}


class FPReplay:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config
        self.cfg = config.get("fp_replay", {})

    def is_enabled(self) -> bool:
        return bool(self.cfg.get("enabled", False))

    def replay(self, vulns: List[Dict]) -> List[Dict]:
        if not self.is_enabled():
            return vulns
        out = []
        for v in vulns:
            if not v.get("false_positive"):
                out.append(v)
                continue
            confirmed = self._reprobe(v)
            if confirmed:
                v = dict(v)
                v["false_positive"] = False
                v["fp_replay"] = "confirmed"
                v["confidence"] = max(float(v.get("confidence") or 0), 0.7)
            else:
                v = dict(v)
                v["fp_replay"] = "still_fp"
            out.append(v)
        return out

    def _reprobe(self, v: Dict) -> bool:
        url = v.get("url") or ""
        param = v.get("parameter") or ""
        t = str(v.get("type", "")).lower()
        if "xss" in t:
            alts = _ALTS["xss"]
        elif "sql" in t:
            alts = _ALTS["sql"]
        else:
            alts = _ALTS["default"]
        for payload in alts:
            try:
                target = url
                if param and "?" in url:
                    p = urlparse(url)
                    qs = parse_qs(p.query, keep_blank_values=True)
                    qs[param] = [payload]
                    target = urlunparse(p._replace(query=urlencode(qs, doseq=True)))
                resp = self.http_client.get(target)
                if not resp:
                    continue
                body = getattr(resp, "text", "") or ""
                if payload in body or payload[:12] in body:
                    return True
            except Exception as e:
                logger.debug(f"fp replay: {e}")
        return False
