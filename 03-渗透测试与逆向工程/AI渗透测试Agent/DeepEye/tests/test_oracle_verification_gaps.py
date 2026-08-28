"""Core multi-surface + RFI/CRLF/LDAP/open_redirect wiring checks."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


class R:
    def __init__(self, status=200, text="", headers=None):
        self.status_code = status
        self.text = text
        self.headers = headers or {}


def test_oast_default_empty():
    from core.ai_payload_generator import AIPayloadGenerator

    g = AIPayloadGenerator(
        MagicMock(),
        {"vulnerability_scanner": {"payload_generation": {"use_ai": False, "cve_database": False}}},
    )
    assert g.OAST_CALLBACK_URL == ""
    assert "example.com" not in " ".join(g._generate_rfi_payloads({}))


def test_rfi_uses_oast_not_example():
    from core.vulnerability_scanner import VulnerabilityScanner
    import inspect

    src = inspect.getsource(VulnerabilityScanner._check_rfi)
    assert "example.com" not in src


def test_crlf_multi_surface_form():
    from core.vulnerability_scanner import VulnerabilityScanner

    class HC:
        def get(self, url, headers=None, allow_redirects=True):
            return R(200, "ok", {})

        def post(self, url, data=None, json=None, headers=None):
            return R(200, "ok", {"Set-Cookie": "test=crlf"})

    vs = VulnerabilityScanner(
        {"vulnerability_scanner": {"enabled_checks": ["crlf_injection"]}},
        HC(),
    )
    ctx = {
        "forms": [
            {
                "action": "/x",
                "method": "POST",
                "inputs": [{"name": "q", "type": "text", "value": ""}],
            }
        ]
    }
    vulns = vs._check_crlf_injection(
        "https://t.com/x",
        ["%0d%0aSet-Cookie:test=crlf"],
        ctx,
    )
    assert any("CRLF" in v.get("type", "") for v in vulns)


def test_ldap_multi_surface_query():
    from core.vulnerability_scanner import VulnerabilityScanner

    class HC:
        def get(self, url, headers=None, allow_redirects=True):
            if "%2A" in url or "*" in url or "objectClass" in url:
                return R(200, "LDAPException bad search filter")
            return R(200, "ok")

        def post(self, *a, **k):
            return R(200, "ok")

    vs = VulnerabilityScanner(
        {"vulnerability_scanner": {"enabled_checks": ["ldap_injection"]}},
        HC(),
    )
    vulns = vs._check_ldap_injection("https://t.com/search?user=a", ["*)(objectClass=*"], {})
    assert any("LDAP" in v.get("type", "") for v in vulns)


def test_open_redirect_payloads_wired():
    from core.vulnerability_scanner import VulnerabilityScanner

    class HC:
        def get(self, url, headers=None, allow_redirects=True):
            if "evil.example" in url:
                return R(302, "", {"Location": "https://evil.example/"})
            return R(200, "ok")

        def post(self, *a, **k):
            return R(200, "ok")

    vs = VulnerabilityScanner(
        {"vulnerability_scanner": {"enabled_checks": ["open_redirect"]}},
        HC(),
    )
    vulns = vs._check_open_redirect(
        "https://t.com/out?next=home",
        ["https://evil.example/"],
        {},
    )
    assert any("Open Redirect" in v.get("type", "") for v in vulns)


def test_feature_modules_registered():
    from core.vulnerability_scanner import VulnerabilityScanner

    class HC:
        def get(self, *a, **k):
            return None

        def post(self, *a, **k):
            return None

    need = [
        "api_bola_deep",
        "websocket_deep",
        "sse_injection",
        "cloud_misconfig",
        "php_webshell",
        "frida_mobile",
        "graphql_deep",
        "idor",
        "ssrf_cloud",
        "stored_xss",
        "email_injection",
    ]
    vs = VulnerabilityScanner(
        {"vulnerability_scanner": {"enabled_checks": need}},
        HC(),
    )
    names = {n for n, _ in vs._feature_testers}
    for c in need:
        assert c in names, f"missing {c}"
