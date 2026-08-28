"""Android APK static heuristics (manifest strings without full apktool)."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

_RISKY = [
    (re.compile(rb"android:debuggable\s*=\s*\"true\"", re.I), "debuggable", "high",
     "android:debuggable=true allows runtime instrumentation"),
    (re.compile(rb"android:allowBackup\s*=\s*\"true\"", re.I), "allowBackup", "medium",
     "android:allowBackup=true enables adb backup of app data"),
    (re.compile(rb"android:usesCleartextTraffic\s*=\s*\"true\"", re.I), "cleartext", "medium",
     "Cleartext HTTP traffic allowed"),
    (re.compile(rb"android:exported\s*=\s*\"true\"", re.I), "exported", "medium",
     "Exported components increase attack surface"),
    (re.compile(rb"MODE_WORLD_READABLE|MODE_WORLD_WRITEABLE", re.I), "world_mode", "high",
     "World-readable/writable file modes"),
    (re.compile(rb"WebView|addJavascriptInterface|setJavaScriptEnabled", re.I), "webview", "medium",
     "WebView / JS bridge patterns detected"),
    (re.compile(rb"http://", re.I), "http_url", "low", "Hardcoded http:// URLs found"),
]


class AndroidStaticTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("android_static") or self.config.get("mobile") or {}

    def scan(self, url: str = "", context: Optional[Dict] = None) -> List[Dict]:
        context = context or {}
        artifact = (
            context.get("artifact")
            or self.cfg.get("artifact")
            or self.cfg.get("apk_path")
            or ""
        )
        if not artifact:
            return []
        path = Path(artifact)
        if not path.exists():
            return [{
                "type": "Android APK Not Found",
                "severity": "info",
                "url": url or artifact,
                "parameter": "artifact",
                "payload": artifact,
                "evidence": "file missing",
                "description": "Cannot static-analyze missing APK",
                "remediation": "Provide valid path in mobile.artifact / android_static.apk_path",
            }]

        blob = b""
        try:
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path, "r") as zf:
                    # AndroidManifest.xml is binary AXML — still scan raw + strings in classes
                    for name in zf.namelist():
                        if name.endswith((".xml", ".json", ".properties", ".js", ".html")):
                            try:
                                blob += zf.read(name)[:200_000]
                            except Exception:
                                pass
                        if len(blob) > 2_000_000:
                            break
                    # also sample dex for strings
                    for name in zf.namelist():
                        if name.endswith(".dex"):
                            try:
                                blob += zf.read(name)[:500_000]
                            except Exception:
                                pass
                            break
            else:
                blob = path.read_bytes()[:2_000_000]
        except Exception as e:
            logger.debug(f"APK read failed: {e}")
            return [{
                "type": "Android APK Read Error",
                "severity": "info",
                "url": url or str(path),
                "parameter": "artifact",
                "payload": str(path),
                "evidence": str(e)[:200],
                "description": "Failed to open APK for static analysis",
                "remediation": "Ensure file is a valid APK/ZIP",
            }]

        findings: List[Dict] = []
        for cre, key, sev, desc in _RISKY:
            if cre.search(blob):
                findings.append({
                    "type": f"Android Static Risk ({key})",
                    "severity": sev,
                    "url": url or str(path),
                    "parameter": key,
                    "payload": str(path.name),
                    "evidence": desc,
                    "description": desc,
                    "remediation": "Harden AndroidManifest and remove insecure flags for release builds",
                })
        # API keys / secrets lite
        for m in re.finditer(rb"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[\"']([^\"']{8,64})[\"']", blob):
            findings.append({
                "type": "Android Hardcoded Secret Pattern",
                "severity": "high",
                "url": url or str(path),
                "parameter": m.group(1).decode("utf-8", "ignore"),
                "payload": m.group(2)[:4].decode("utf-8", "ignore") + "***",
                "evidence": "Possible hardcoded credential string in package",
                "description": "Hardcoded secrets in mobile package increase reverse-engineering risk",
                "remediation": "Move secrets to server-side; use Android Keystore",
            })
            if len(findings) > 30:
                break
        return findings
