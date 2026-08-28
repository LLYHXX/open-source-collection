"""AI payload generator — XSS/SQL split and defaults (T1)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.ai_payload_generator import AIPayloadGenerator


def _gen():
    g = AIPayloadGenerator(ai_manager=MagicMock(), config={
        "vulnerability_scanner": {
            "payload_generation": {"use_ai": False, "cve_database": False}
        }
    })
    g.OAST_CALLBACK_URL = "http://oast.test/cb"
    return g


def test_generate_xss_payloads_exists_and_looks_like_xss():
    g = _gen()
    payloads = g._generate_xss_payloads({}, [], False)
    assert len(payloads) >= 8
    markers = ("<", "onerror", "onload", "javascript", "svg", "script", "alert")
    assert all(any(m in p.lower() for m in markers) for p in payloads)
    assert not any(" or " in p.lower() and "1=1" in p.replace(" ", "") for p in payloads)


def test_sql_payloads_have_no_xss_markers():
    g = _gen()
    payloads = g._generate_sql_payloads({}, [], False)
    assert len(payloads) >= 5
    bad = ("<script", "<svg", "<img", "onerror", "onload", "javascript:")
    for p in payloads:
        low = p.lower()
        assert not any(b in low for b in bad), f"SQL payload contaminated with XSS: {p!r}"


def test_default_payloads_has_core_keys():
    g = _gen()
    d = g._get_default_payloads()
    expected = {
        "sql_injection",
        "xss",
        "command_injection",
        "ssrf",
        "xxe",
        "path_traversal",
        "lfi",
        "ssti",
        "ldap_injection",
        "crlf_injection",
        "open_redirect",
        "nosql_injection",
    }
    assert expected.issubset(set(d.keys()))
    for k in expected:
        assert len(d[k]) >= 1


def test_ai_enrich_calls_generate():
    ai = MagicMock()
    ai.generate.return_value = "' OR 1=1--\n' UNION SELECT NULL--"
    g = AIPayloadGenerator(
        ai_manager=ai,
        config={
            "vulnerability_scanner": {
                "payload_generation": {"use_ai": True, "cve_database": False}
            }
        },
    )
    g.OAST_CALLBACK_URL = "http://oast.test/cb"
    out = g.generate_payloads({"url": "https://x.com/?q=1", "headers": {"server": "nginx"}})
    assert ai.generate.called
    assert "sql_injection" in out
    assert any("OR" in p.upper() or "UNION" in p.upper() for p in out["sql_injection"])


def test_extract_input_fields_from_forms():
    g = _gen()
    result = g._extract_input_fields({
        "forms": [
            {
                "action": "/login",
                "method": "POST",
                "inputs": [
                    {"name": "user", "type": "text", "value": ""},
                    {"name": "pass", "type": "password", "value": ""},
                ],
            }
        ]
    })
    assert "user" in result and "pass" in result
    assert "To be implemented" not in result


def test_generate_payloads_no_ai_returns_xss_key():
    g = _gen()
    out = g.generate_payloads({"url": "https://x.com/?q=1", "headers": {}})
    assert "xss" in out
    assert len(out["xss"]) >= 1
