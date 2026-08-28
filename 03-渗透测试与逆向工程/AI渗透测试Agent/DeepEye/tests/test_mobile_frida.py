"""Mobile / Frida + AI attack chain tests."""
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_frida_generates_scripts(tmp_path):
    from modules.frida_mobile import FridaMobileTester

    cfg = {
        "frida_mobile": {
            "platform": "android",
            "package": "com.example.app",
            "script_output_dir": str(tmp_path / "scripts"),
            "use_ai": False,
            "try_attach": False,
        }
    }
    t = FridaMobileTester(MagicMock(), cfg)
    findings = t.scan(context={"platform": "android", "package": "com.example.app"})
    assert findings
    assert any("Frida" in f.get("type", "") for f in findings)
    scripts = list((tmp_path / "scripts").glob("*.js"))
    assert scripts
    assert any("attack_chain" in f for f in findings)


def test_frida_ai_advice_populates_chain():
    from modules.frida_mobile import FridaMobileTester

    ai = MagicMock()
    ai.generate.return_value = (
        '{"hooks":["hook Cipher"],"payloads":["frida -U -f pkg -l x.js"],'
        '"attack_chain":["static","pinning bypass","api replay"],"notes":"order matters"}'
    )
    t = FridaMobileTester(
        MagicMock(),
        {"frida_mobile": {"use_ai": True, "script_output_dir": "reports/frida_scripts", "try_attach": False}},
    )
    t.set_ai_manager(ai)
    findings = t.scan(context={"platform": "android", "package": "com.demo"})
    pack = next(f for f in findings if "Hook Pack" in f.get("type", ""))
    assert pack.get("attack_chain")
    assert pack.get("ai_payload_advice")
    assert "hook" in pack["ai_payload_advice"].lower() or "HOOKS" in pack["ai_payload_advice"]


def test_android_static_detects_debuggable(tmp_path):
    from modules.android_static import AndroidStaticTester

    apk = tmp_path / "app.apk"
    with zipfile.ZipFile(apk, "w") as zf:
        zf.writestr(
            "AndroidManifest.xml",
            b'<manifest android:debuggable="true" android:allowBackup="true" '
            b'android:usesCleartextTraffic="true"></manifest>',
        )
        zf.writestr("res/values/strings.xml", b"<string>api_key=supersecret123</string>")

    t = AndroidStaticTester(MagicMock(), {"android_static": {"artifact": str(apk)}})
    findings = t.scan(context={"artifact": str(apk)})
    types = " ".join(f.get("type", "") for f in findings)
    assert "debuggable" in types.lower() or "Android Static" in types


def test_ios_plist_ats(tmp_path):
    import plistlib
    from modules.ios_plist import IOSPlistTester

    plist_path = tmp_path / "Info.plist"
    data = {
        "NSAppTransportSecurity": {"NSAllowsArbitraryLoads": True},
        "CFBundleURLTypes": [{"CFBundleURLSchemes": ["myapp"]}],
    }
    plist_path.write_bytes(plistlib.dumps(data))
    t = IOSPlistTester(MagicMock(), {"ios_plist": {"artifact": str(plist_path)}})
    findings = t.scan(context={"artifact": str(plist_path)})
    assert any("ATS" in f.get("type", "") for f in findings)
    assert any("URL Scheme" in f.get("type", "") for f in findings)


def test_mobile_ai_chain_baseline():
    from modules.mobile_ai_chain import MobileAIAttackChain

    t = MobileAIAttackChain(
        MagicMock(),
        {"mobile_ai_chain": {"use_ai": False, "platform": "android"}},
    )
    findings = t.scan(context={"platform": "android", "package": "com.x", "mobile_findings": []})
    assert findings
    assert findings[0].get("attack_chain")
    assert findings[0].get("suggested_payloads")


def test_mobile_ssl_pinning_indicator(tmp_path):
    from modules.mobile_ssl_pinning import MobileSSLPinningTester

    apk = tmp_path / "p.apk"
    with zipfile.ZipFile(apk, "w") as zf:
        zf.writestr("classes.dex", b"xx CertificatePinner OkHttpClient yy")
    t = MobileSSLPinningTester(MagicMock(), {"mobile": {"artifact": str(apk)}})
    findings = t.scan(context={"artifact": str(apk)})
    assert any("Pinning" in f.get("type", "") for f in findings)


def test_feature_testers_include_mobile_and_api():
    from core.vulnerability_scanner import VulnerabilityScanner

    class HC:
        def get(self, *a, **k):
            return None

        def post(self, *a, **k):
            return None

    checks = [
        "api_bola_deep",
        "websocket_deep",
        "sse_injection",
        "cloud_misconfig",
        "php_webshell",
        "frida_mobile",
        "android_static",
        "ios_plist",
        "mobile_ssl_pinning",
        "mobile_ai_chain",
    ]
    vs = VulnerabilityScanner(
        {"vulnerability_scanner": {"enabled_checks": checks}},
        HC(),
    )
    names = {n for n, _ in vs._feature_testers}
    for c in checks:
        assert c in names, f"missing {c}"


def test_scanner_engine_mobile_phase(tmp_path):
    from core.scanner_engine import ScannerEngine

    apk = tmp_path / "a.apk"
    with zipfile.ZipFile(apk, "w") as zf:
        zf.writestr("AndroidManifest.xml", b'android:debuggable="true"')

    config = {
        "scanner": {},
        "vulnerability_scanner": {
            "enabled_checks": ["android_static", "frida_mobile", "mobile_ai_chain"],
            "payload_generation": {"use_ai": False, "cve_database": False},
        },
        "secrets_scanner": {"enabled": False},
        "plugin_manager": {"enabled": False},
        "advanced": {},
        "experimental": {"enable_cve_matching": False},
        "ai_providers": {},
        "mobile": {
            "enabled": True,
            "platform": "android",
            "package": "com.test",
            "artifact": str(apk),
            "use_ai": False,
            "script_output_dir": str(tmp_path / "frida"),
            "try_attach": False,
        },
        "frida_mobile": {
            "use_ai": False,
            "script_output_dir": str(tmp_path / "frida"),
            "try_attach": False,
        },
    }
    eng = ScannerEngine(
        target_url="https://example.com",
        config=config,
        ai_manager=MagicMock(),
        depth=1,
        threads=1,
    )
    # run only mobile phase logic by calling scan with quick empty crawl hard
    # Directly invoke mobile block via scan with max isolation: mock crawl
    eng.crawl_recursive = lambda: set()
    eng.scan_all_urls = lambda urls, recon=None: None
    eng.run_reconnaissance = lambda: {}
    results = eng.scan(enable_recon=False, full_scan=False, quick_scan=True, scan_subdomains=False)
    assert results.get("mobile_findings", 0) >= 1 or any(
        v.get("source") == "mobile" for v in eng.vulnerabilities
    )
