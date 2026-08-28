"""iOS Info.plist / ATS / URL scheme static checks."""
from __future__ import annotations

import plistlib
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class IOSPlistTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("ios_plist") or self.config.get("mobile") or {}

    def scan(self, url: str = "", context: Optional[Dict] = None) -> List[Dict]:
        context = context or {}
        artifact = (
            context.get("artifact")
            or self.cfg.get("artifact")
            or self.cfg.get("ipa_path")
            or self.cfg.get("plist_path")
            or ""
        )
        if not artifact:
            return []
        path = Path(artifact)
        if not path.exists():
            return [{
                "type": "iOS Artifact Not Found",
                "severity": "info",
                "url": url or artifact,
                "parameter": "artifact",
                "payload": artifact,
                "evidence": "missing",
                "description": "IPA/plist path not found",
                "remediation": "Set mobile.artifact to IPA or Info.plist",
            }]

        plists = self._load_plists(path)
        findings: List[Dict] = []
        for name, data in plists:
            findings.extend(self._analyze_plist(name, data, url or str(path)))
        if not plists and path.suffix.lower() == ".plist":
            try:
                data = plistlib.loads(path.read_bytes())
                findings.extend(self._analyze_plist(path.name, data, url or str(path)))
            except Exception as e:
                findings.append({
                    "type": "iOS Plist Parse Error",
                    "severity": "info",
                    "url": url or str(path),
                    "parameter": "plist",
                    "payload": str(path),
                    "evidence": str(e)[:200],
                    "description": "Could not parse plist",
                    "remediation": "Provide binary or XML Info.plist",
                })
        return findings

    def _load_plists(self, path: Path) -> List[tuple]:
        out = []
        if path.suffix.lower() == ".plist":
            try:
                out.append((path.name, plistlib.loads(path.read_bytes())))
            except Exception:
                pass
            return out
        if not zipfile.is_zipfile(path):
            return out
        try:
            with zipfile.ZipFile(path, "r") as zf:
                for name in zf.namelist():
                    if name.endswith("Info.plist"):
                        try:
                            out.append((name, plistlib.loads(zf.read(name))))
                        except Exception:
                            # sometimes XML plist
                            try:
                                raw = zf.read(name)
                                if raw.strip().startswith(b"<?xml") or b"<plist" in raw[:200]:
                                    out.append((name, plistlib.loads(raw)))
                            except Exception:
                                pass
        except Exception as e:
            logger.debug(f"ipa read: {e}")
        return out

    def _analyze_plist(self, name: str, data: Any, target: str) -> List[Dict]:
        if not isinstance(data, dict):
            return []
        findings = []
        ats = data.get("NSAppTransportSecurity") or {}
        if isinstance(ats, dict):
            if ats.get("NSAllowsArbitraryLoads"):
                findings.append({
                    "type": "iOS ATS Allows Arbitrary Loads",
                    "severity": "high",
                    "url": target,
                    "parameter": "NSAllowsArbitraryLoads",
                    "payload": name,
                    "evidence": "NSAppTransportSecurity.NSAllowsArbitraryLoads=true",
                    "description": "App Transport Security disabled for arbitrary loads",
                    "remediation": "Disable NSAllowsArbitraryLoads; use exception domains sparingly",
                })
            exceptions = ats.get("NSExceptionDomains") or {}
            if isinstance(exceptions, dict) and exceptions:
                findings.append({
                    "type": "iOS ATS Exception Domains",
                    "severity": "medium",
                    "url": target,
                    "parameter": "NSExceptionDomains",
                    "payload": ",".join(list(exceptions.keys())[:10]),
                    "evidence": f"{len(exceptions)} ATS exception domain(s)",
                    "description": "ATS exceptions may allow insecure HTTP to listed domains",
                    "remediation": "Minimize ATS exceptions; require TLS 1.2+",
                })

        schemes = data.get("CFBundleURLTypes") or []
        if schemes:
            scheme_names = []
            for s in schemes:
                if isinstance(s, dict):
                    scheme_names.extend(s.get("CFBundleURLSchemes") or [])
            if scheme_names:
                findings.append({
                    "type": "iOS Custom URL Schemes",
                    "severity": "medium",
                    "url": target,
                    "parameter": "CFBundleURLSchemes",
                    "payload": ",".join(str(x) for x in scheme_names[:15]),
                    "evidence": "Custom URL schemes registered",
                    "description": "URL schemes can enable deep-link / IPC abuse",
                    "remediation": "Validate deep-link inputs; prefer universal links",
                })

        if data.get("UIFileSharingEnabled"):
            findings.append({
                "type": "iOS UIFileSharingEnabled",
                "severity": "medium",
                "url": target,
                "parameter": "UIFileSharingEnabled",
                "payload": name,
                "evidence": "UIFileSharingEnabled=true",
                "description": "Users can access app documents via Finder/iTunes",
                "remediation": "Disable file sharing unless required",
            })
        return findings
