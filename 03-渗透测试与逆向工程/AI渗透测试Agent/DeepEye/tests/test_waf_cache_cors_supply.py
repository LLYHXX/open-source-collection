"""WAF profile apply + cache/cors/supply chain enhancements."""
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


def test_waf_profile_mutates_payloads():
    from core.ai_payload_generator import AIPayloadGenerator

    g = AIPayloadGenerator(
        MagicMock(),
        {"vulnerability_scanner": {"payload_generation": {"use_ai": False, "cve_database": False}}},
    )
    base = ["' OR 1=1--", "<script>alert(1)</script>"]
    out = g._apply_waf_profile(
        base,
        {"prefer_encoding": ["url", "case_swap", "comment_insert"], "case_swap": True, "avoid": ["script_tag_raw"]},
    )
    assert len(out) >= len(base)
    assert not any("<script" in p.lower() for p in out)
    assert any("%" in p or "/**/" in p or p != p.lower() for p in out)


def test_generate_payloads_uses_waf_headers():
    from core.ai_payload_generator import AIPayloadGenerator

    g = AIPayloadGenerator(
        MagicMock(),
        {"vulnerability_scanner": {"payload_generation": {"use_ai": True, "cve_database": False}}},
    )
    out = g.generate_payloads({
        "url": "https://x.com/?q=1",
        "headers": {"cf-ray": "abc", "server": "cloudflare"},
    })
    assert "sql_injection" in out and len(out["sql_injection"]) >= 5


def test_cache_deception_sensitive_static_path():
    from modules.cache_deception import CacheDeceptionTester

    class HC:
        def get(self, url, headers=None):
            if url.endswith(".css") or "%2f.css" in url or "/;.css" in url:
                return R(
                    200,
                    "welcome email logout password session csrf " + "x" * 100,
                    {"Cache-Control": "public, max-age=3600"},
                )
            return R(200, "welcome email logout password session csrf " + "x" * 100)

    t = CacheDeceptionTester(HC(), {})
    vulns = t.scan("https://x.com/account/settings")
    assert any("Cache" in v.get("type", "") for v in vulns)


def test_cors_preflight_and_reflection():
    from modules.cors_csp import CorsCspTester

    class HC:
        def get(self, url, headers=None):
            origin = (headers or {}).get("Origin", "")
            return R(
                200,
                "ok",
                {
                    "Access-Control-Allow-Origin": origin or "*",
                    "Access-Control-Allow-Credentials": "true",
                    "Content-Security-Policy": "script-src * 'unsafe-inline'",
                },
            )

        def request(self, method, url, headers=None):
            return R(
                200,
                "",
                {
                    "Access-Control-Allow-Origin": "https://evil.example",
                    "Access-Control-Allow-Methods": "GET,PUT,POST",
                    "Access-Control-Allow-Headers": "Authorization, X-Custom-Auth",
                },
            )

    t = CorsCspTester(HC(), {})
    vulns = t.scan("https://api.example.com/data")
    types = " ".join(v.get("type", "") for v in vulns)
    assert "CORS" in types or "CSP" in types


def test_supply_chain_sri_and_old_jquery():
    from modules.supply_chain_js import SupplyChainJSTester

    html = '''
    <script src="https://cdn.example.com/jquery-1.12.4.min.js"></script>
    <script src="https://cdn.example.com/app.js"></script>
    '''
    class HC:
        def get(self, url, headers=None):
            return R(200, html)

    t = SupplyChainJSTester(HC(), {})
    vulns = t.scan("https://victim.com/", {"response": R(200, html)})
    types = " ".join(v.get("type", "") for v in vulns)
    assert "SRI" in types or "Outdated" in types


def test_templates_exist():
    root = REPO_ROOT / "templates" / "exposures"
    assert (root / "backup-file-exposure.yaml").is_file()
    assert (root / "swagger-ui-exposure.yaml").is_file()
