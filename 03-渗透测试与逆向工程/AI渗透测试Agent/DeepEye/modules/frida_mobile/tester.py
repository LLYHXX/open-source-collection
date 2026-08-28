"""Frida-based mobile dynamic analysis helpers + AI hook advice.

Works offline without Frida installed (static script generation).
When frida is available, can attach and run generated scripts.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

# Built-in Frida script templates (Android / iOS common hooks)
_HOOK_TEMPLATES = {
    "ssl_pinning_android": r"""
// SSL pinning bypass (Android common patterns)
Java.perform(function () {
  try {
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    var TrustManagers = [X509TrustManager.$new({
      checkClientTrusted: function (chain, authType) {},
      checkServerTrusted: function (chain, authType) {},
      getAcceptedIssuers: function () { return []; }
    })];
    var sslContext = SSLContext.getInstance('TLS');
    sslContext.init(null, TrustManagers, null);
    SSLContext.setDefault(sslContext);
    console.log('[+] SSLContext pinning bypass installed');
  } catch (e) { console.log('[-] SSLContext: ' + e); }
  try {
    var OkHttpClient = Java.use('okhttp3.OkHttpClient$Builder');
    OkHttpClient.certificatePinner.implementation = function () { return this; };
    console.log('[+] OkHttp certificatePinner bypass');
  } catch (e) {}
});
""",
    "root_detection_android": r"""
Java.perform(function () {
  var RootBeer = null;
  try {
    var File = Java.use('java.io.File');
    File.exists.implementation = function () {
      var p = this.getAbsolutePath();
      if (p.indexOf('su') >= 0 || p.indexOf('magisk') >= 0) return false;
      return this.exists();
    };
    console.log('[+] File.exists root path filter');
  } catch (e) {}
  try {
    var Runtime = Java.use('java.lang.Runtime');
    Runtime.exec.overload('[Ljava.lang.String;').implementation = function (cmd) {
      var s = cmd.join(' ');
      if (s.indexOf('su') >= 0) throw new Error('blocked');
      return this.exec(cmd);
    };
  } catch (e) {}
});
""",
    "crypto_android": r"""
Java.perform(function () {
  try {
    var Cipher = Java.use('javax.crypto.Cipher');
    Cipher.getInstance.overload('java.lang.String').implementation = function (t) {
      console.log('[crypto] Cipher.getInstance ' + t);
      return this.getInstance(t);
    };
  } catch (e) {}
  try {
    var SecretKeySpec = Java.use('javax.crypto.spec.SecretKeySpec');
    SecretKeySpec.$init.overload('[B', 'java.lang.String').implementation = function (key, algo) {
      console.log('[crypto] SecretKeySpec algo=' + algo + ' keyLen=' + key.length);
      return this.$init(key, algo);
    };
  } catch (e) {}
});
""",
    "ssl_pinning_ios": r"""
// iOS SSL / ATS related hooks (Frida ObjC)
if (ObjC.available) {
  try {
    var NSURLSession = ObjC.classes.NSURLSession;
    Interceptor.attach(ObjC.classes.NSURLSession['- dataTaskWithRequest:completionHandler:'].implementation, {
      onEnter: function (args) { console.log('[ios] NSURLSession request'); }
    });
  } catch (e) { console.log('[-] ios session: ' + e); }
  try {
    var SecTrustEvaluate = Module.findExportByName('Security', 'SecTrustEvaluate');
    if (SecTrustEvaluate) {
      Interceptor.replace(SecTrustEvaluate, new NativeCallback(function (trust, result) {
        Memory.writeU8(result, 1);
        return 0;
      }, 'int', ['pointer', 'pointer']));
      console.log('[+] SecTrustEvaluate bypass');
    }
  } catch (e) {}
}
""",
    "keystore_android": r"""
Java.perform(function () {
  try {
    var KeyStore = Java.use('java.security.KeyStore');
    KeyStore.getKey.overload('java.lang.String', '[C').implementation = function (alias, pass) {
      console.log('[keystore] getKey alias=' + alias);
      return this.getKey(alias, pass);
    };
  } catch (e) {}
});
""",
}


class FridaMobileTester:
    """Generate / optionally run Frida hooks; AI suggests extra hooks + attack chain."""

    def __init__(self, http_client, config: Dict):
        # http_client unused for pure mobile static path; kept for interface parity
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("frida_mobile") or self.config.get("mobile") or {}
        self.ai_manager = None
        self.out_dir = Path(self.cfg.get("script_output_dir", "reports/frida_scripts"))
        self.platform = str(self.cfg.get("platform", "android")).lower()
        self.package = self.cfg.get("package") or self.cfg.get("bundle_id") or ""
        self.device = self.cfg.get("device") or ""
        self.use_ai = bool(self.cfg.get("use_ai", True))
        self.spawn = bool(self.cfg.get("spawn", False))

    def set_ai_manager(self, ai_manager) -> None:
        self.ai_manager = ai_manager

    def frida_available(self) -> bool:
        return shutil.which("frida") is not None

    def scan(self, url: str = "", context: Optional[Dict] = None) -> List[Dict]:
        """Produce mobile dynamic-analysis findings + write Frida scripts."""
        context = context or {}
        vulns: List[Dict] = []
        platform = (context.get("platform") or self.platform or "android").lower()
        package = context.get("package") or self.package or "com.example.app"
        target_label = package or url or "mobile-app"

        scripts = self._select_scripts(platform)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for name, body in scripts.items():
            path = self.out_dir / f"{platform}_{name}.js"
            path.write_text(body.strip() + "\n", encoding="utf-8")
            written.append(str(path))

        # AI advice: extra hooks + attack chain
        ai_advice = ""
        attack_chain: List[str] = []
        if self.use_ai and (self.ai_manager or context.get("ai_manager")):
            ai = self.ai_manager or context.get("ai_manager")
            try:
                ai_advice, attack_chain = self._ai_advice(ai, platform, package, context)
            except Exception as e:
                logger.debug(f"Frida AI advice failed: {e}")

        if ai_advice:
            advice_path = self.out_dir / f"{platform}_{package.replace('.', '_')}_ai_hooks.js"
            advice_path.write_text(
                f"// AI-suggested Frida notes for {package}\n/*\n{ai_advice}\n*/\n",
                encoding="utf-8",
            )
            written.append(str(advice_path))

        # Finding: scripts generated
        vulns.append({
            "type": "Mobile Frida Hook Pack Generated",
            "severity": "info",
            "url": target_label,
            "parameter": platform,
            "payload": "; ".join(scripts.keys()),
            "evidence": f"Wrote {len(written)} Frida script(s) to {self.out_dir}",
            "description": (
                f"Generated Frida hooks for {platform} package={package}. "
                "Use with: frida -U -f <package> -l <script.js> --no-pause"
            ),
            "remediation": "Review hooks only on authorized apps; remove debug builds from production",
            "frida_scripts": written,
            "attack_chain": attack_chain,
            "ai_payload_advice": ai_advice[:4000] if ai_advice else "",
        })

        if not self.frida_available():
            vulns.append({
                "type": "Frida CLI Not Installed",
                "severity": "info",
                "url": target_label,
                "parameter": "frida",
                "payload": "",
                "evidence": "frida not found on PATH",
                "description": "Install Frida tools for live attach: pip install frida-tools",
                "remediation": "pip install frida-tools && frida --version",
            })
        elif self.cfg.get("try_attach", False) and package:
            attach_result = self._try_attach(package, written[0] if written else "")
            if attach_result:
                vulns.append(attach_result)

        # Static risk heuristics from context path (APK/IPA path)
        artifact = context.get("artifact") or self.cfg.get("artifact") or ""
        if artifact:
            vulns.extend(self._artifact_hints(artifact, platform, target_label))

        return vulns

    def _select_scripts(self, platform: str) -> Dict[str, str]:
        if platform in ("ios", "iphone", "ipad"):
            return {
                "ssl_pinning_ios": _HOOK_TEMPLATES["ssl_pinning_ios"],
            }
        return {
            "ssl_pinning_android": _HOOK_TEMPLATES["ssl_pinning_android"],
            "root_detection_android": _HOOK_TEMPLATES["root_detection_android"],
            "crypto_android": _HOOK_TEMPLATES["crypto_android"],
            "keystore_android": _HOOK_TEMPLATES["keystore_android"],
        }

    def _ai_advice(self, ai, platform: str, package: str, context: Dict):
        recon = context.get("mobile_recon") or {}
        prompt = (
            "You are a senior mobile pentester. Platform={platform}, package={package}. "
            "Known facts: {facts}. "
            "Reply with JSON only: "
            '{{"hooks":["frida hook idea 1","..."],'
            '"payloads":["payload or test vector 1","..."],'
            '"attack_chain":["step1","step2","step3"],'
            '"notes":"short advice"}}. '
            "Focus on SSL pinning, root/jailbreak bypass, crypto keys, deep links, IPC, storage."
        ).format(
            platform=platform,
            package=package,
            facts=json.dumps(recon)[:800],
        )
        raw = (ai.generate(prompt) or "").strip()
        chain: List[str] = []
        advice = raw
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(raw[start : end + 1])
                hooks = data.get("hooks") or []
                payloads = data.get("payloads") or []
                chain = list(data.get("attack_chain") or [])
                notes = data.get("notes") or ""
                advice = (
                    "HOOKS:\n- "
                    + "\n- ".join(str(h) for h in hooks[:12])
                    + "\n\nPAYLOADS:\n- "
                    + "\n- ".join(str(p) for p in payloads[:12])
                    + "\n\nCHAIN:\n- "
                    + "\n- ".join(str(s) for s in chain[:10])
                    + "\n\nNOTES:\n"
                    + str(notes)
                )
        except Exception:
            pass
        if not chain:
            chain = self._default_chain(platform)
        return advice, chain

    def _default_chain(self, platform: str) -> List[str]:
        if platform in ("ios", "iphone", "ipad"):
            return [
                "Inventory IPA / Info.plist ATS settings",
                "Bypass SSL pinning (SecTrustEvaluate)",
                "Hook keychain / NSURLSession for secrets",
                "Test deep links and URL schemes",
                "Capture tokens → replay API with mitm",
            ]
        return [
            "Decompile APK (manifest, debuggable, backup)",
            "Bypass root detection + SSL pinning with Frida",
            "Hook Cipher/KeyStore for secrets",
            "Tamper shared prefs / SQLite / WebView JS bridges",
            "Deep-link / IPC export abuse",
            "Replay captured API with mobile tokens",
        ]

    def _try_attach(self, package: str, script_path: str) -> Optional[Dict]:
        import subprocess
        try:
            cmd = ["frida", "-U", "-l", script_path, "-n", package]
            if self.spawn:
                cmd = ["frida", "-U", "-f", package, "-l", script_path, "--no-pause"]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=int(self.cfg.get("attach_timeout", 8)),
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode == 0 or "Attached" in out or "[+]" in out:
                return {
                    "type": "Frida Attach Success",
                    "severity": "info",
                    "url": package,
                    "parameter": "frida",
                    "payload": " ".join(cmd),
                    "evidence": out[:500],
                    "description": "Frida attached and ran generated script",
                    "remediation": "Ensure production builds use hardening (RASP, pinning integrity)",
                }
            return {
                "type": "Frida Attach Failed",
                "severity": "low",
                "url": package,
                "parameter": "frida",
                "payload": " ".join(cmd),
                "evidence": out[:500] or f"exit={proc.returncode}",
                "description": "Could not attach Frida (device offline, no frida-server, wrong package)",
                "remediation": "Start frida-server on device; match frida-tools version",
            }
        except Exception as e:
            return {
                "type": "Frida Attach Error",
                "severity": "info",
                "url": package,
                "parameter": "frida",
                "payload": "",
                "evidence": str(e)[:300],
                "description": "Frida attach raised exception",
                "remediation": "Install frida-tools and connected device with frida-server",
            }

    def _artifact_hints(self, artifact: str, platform: str, target: str) -> List[Dict]:
        path = Path(artifact)
        if not path.exists():
            return [{
                "type": "Mobile Artifact Missing",
                "severity": "info",
                "url": target,
                "parameter": "artifact",
                "payload": artifact,
                "evidence": "path does not exist",
                "description": "Configured mobile artifact not found for static analysis",
                "remediation": "Set mobile.artifact to valid APK/IPA path",
            }]
        findings = []
        name = path.name.lower()
        if name.endswith(".apk") or platform == "android":
            findings.append({
                "type": "Android APK Artifact Present",
                "severity": "info",
                "url": target,
                "parameter": "artifact",
                "payload": str(path),
                "evidence": f"size={path.stat().st_size}",
                "description": "APK available for static analysis (android_static module)",
                "remediation": "Run android_static + Frida dynamic hooks on authorized build",
            })
        if name.endswith((".ipa", ".app")) or platform == "ios":
            findings.append({
                "type": "iOS Artifact Present",
                "severity": "info",
                "url": target,
                "parameter": "artifact",
                "payload": str(path),
                "evidence": f"size={path.stat().st_size}",
                "description": "iOS package available for plist/ATS review",
                "remediation": "Run ios_plist + Frida iOS hooks on authorized build",
            })
        return findings
