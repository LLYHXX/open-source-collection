"""AI-driven mobile attack chain planner + payload advisor.

Combines recon findings into ordered attack steps and suggested payloads.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class MobileAIAttackChain:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("mobile_ai_chain") or self.config.get("mobile") or {}
        self.ai_manager = None

    def set_ai_manager(self, ai_manager) -> None:
        self.ai_manager = ai_manager

    def scan(self, url: str = "", context: Optional[Dict] = None) -> List[Dict]:
        context = context or {}
        ai = self.ai_manager or context.get("ai_manager")
        platform = (context.get("platform") or self.cfg.get("platform") or "android").lower()
        package = context.get("package") or self.cfg.get("package") or "app"
        prior = context.get("mobile_findings") or context.get("findings") or []

        # deterministic baseline chain
        chain = self._baseline_chain(platform, prior)
        payloads = self._baseline_payloads(platform)
        notes = "Heuristic mobile attack chain (AI disabled or unavailable)."

        if ai and self.cfg.get("use_ai", True):
            try:
                prompt = self._prompt(platform, package, prior, chain)
                raw = (ai.generate(prompt) or "").strip()
                parsed = self._parse(raw)
                if parsed.get("attack_chain"):
                    chain = [str(x) for x in parsed["attack_chain"][:15]]
                if parsed.get("payloads"):
                    payloads = [str(x) for x in parsed["payloads"][:20]]
                if parsed.get("notes"):
                    notes = str(parsed["notes"])[:2000]
            except Exception as e:
                logger.debug(f"mobile AI chain: {e}")

        return [{
            "type": "Mobile AI Attack Chain",
            "severity": "info",
            "url": package or url or "mobile",
            "parameter": platform,
            "payload": " | ".join(payloads[:5]),
            "evidence": notes,
            "description": "AI/heuristic ordered mobile attack chain with payload advice",
            "remediation": "Execute chain only on authorized builds; document findings per step",
            "attack_chain": chain,
            "suggested_payloads": payloads,
            "ai_payload_advice": notes,
        }]

    def _baseline_chain(self, platform: str, prior: List) -> List[str]:
        pins = any("pinning" in str(p.get("type", "")).lower() for p in prior if isinstance(p, dict))
        debuggable = any("debuggable" in str(p.get("type", "")).lower() for p in prior if isinstance(p, dict))
        chain = []
        if platform in ("ios", "iphone"):
            chain = [
                "Static: Info.plist ATS + URL schemes (ios_plist)",
                "Dynamic: Frida SSL trust bypass",
                "Hook keychain / NSUserDefaults",
                "Deep link fuzzing",
                "API token replay via proxy",
            ]
        else:
            chain = [
                "Static: manifest flags (android_static)",
                "Dynamic: Frida root + SSL pinning bypass",
                "Hook Cipher/KeyStore for secrets",
                "Exported component / deep-link abuse",
                "WebView JS bridge tests",
                "API replay with stolen tokens",
            ]
        if pins:
            chain.insert(1, "Prioritize SSL pinning bypass before traffic analysis")
        if debuggable:
            chain.insert(0, "Debuggable build — attach debugger/Frida early")
        return chain

    def _baseline_payloads(self, platform: str) -> List[str]:
        common = [
            "frida -U -f <package> -l ssl_pinning.js --no-pause",
            "adb backup -f backup.ab <package>",
            "objection -g <package> explore",
            "mitmproxy with mobile cert + pinning bypass",
        ]
        if platform in ("ios", "iphone"):
            common.append("frida -U -n <app> -l ssl_pinning_ios.js")
        else:
            common.extend([
                "adb shell am start -a android.intent.action.VIEW -d 'app://evil'",
                "drozer console connect → run app.package.attacksurface",
            ])
        return common

    def _prompt(self, platform, package, prior, chain) -> str:
        brief = [
            {"type": p.get("type"), "sev": p.get("severity")}
            for p in prior[:20]
            if isinstance(p, dict)
        ]
        return (
            "Mobile red-team planner. "
            f"platform={platform} package={package} prior_findings={json.dumps(brief)}. "
            f"baseline_chain={chain}. "
            "Return JSON only: "
            '{"attack_chain":["..."],"payloads":["frida/adb/objection commands or test vectors"],'
            '"notes":"why this order"}'
        )

    def _parse(self, raw: str) -> Dict:
        try:
            s, e = raw.find("{"), raw.rfind("}")
            if s >= 0 and e > s:
                return json.loads(raw[s : e + 1])
        except Exception:
            pass
        return {}
