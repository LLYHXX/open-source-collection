"""Tests for CRLFHeaderInjectDeepTester."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


class _Resp:
    def __init__(self, text: str = "", headers=None, status_code: int = 200):
        self.text = text
        self.headers = headers or {}
        self.status_code = status_code


class _HC:
    def __init__(self, resp):
        self._resp = resp

    def get(self, url, headers=None):
        return self._resp


def test_no_query_params_returns_empty():
    from modules.crlf_header_inject_deep import CRLFHeaderInjectDeepTester

    t = CRLFHeaderInjectDeepTester(_HC(_Resp()), {})
    assert t.scan("https://example.com/path") == []


def test_header_marker_detected():
    from modules.crlf_header_inject_deep import CRLFHeaderInjectDeepTester

    resp = _Resp(headers={"Set-Cookie": "deep-eye-crlf=1; Path=/"})
    t = CRLFHeaderInjectDeepTester(_HC(resp), {})
    vulns = t.scan("https://example.com/page?q=1")
    assert len(vulns) == 1
    assert vulns[0]["type"] == "CRLF Header Injection (Deep)"
    assert vulns[0]["severity"] == "high"
    assert vulns[0]["parameter"] == "q"
    assert "deep-eye-crlf" in vulns[0]["evidence"]


def test_response_split_detected():
    from modules.crlf_header_inject_deep import CRLFHeaderInjectDeepTester

    resp = _Resp(text="some body HTTP/1.1 200 OK Content-Length: 2 OK")
    t = CRLFHeaderInjectDeepTester(_HC(resp), {})
    vulns = t.scan("https://example.com/page?q=1")
    assert len(vulns) == 1
    assert vulns[0]["type"] == "HTTP Response Splitting (CRLF Deep)"
    assert vulns[0]["severity"] == "critical"
    assert vulns[0]["parameter"] == "q"


def test_no_vulnerability_returns_empty():
    from modules.crlf_header_inject_deep import CRLFHeaderInjectDeepTester

    resp = _Resp(text="normal body", headers={"Content-Type": "text/html"})
    t = CRLFHeaderInjectDeepTester(_HC(resp), {})
    vulns = t.scan("https://example.com/page?q=1")
    assert vulns == []


def test_scanner_registers_feature_tester():
    from core.vulnerability_scanner import VulnerabilityScanner

    class HC:
        def get(self, *a, **k):
            return None

    vs = VulnerabilityScanner(
        {
            "vulnerability_scanner": {
                "enabled_checks": ["crlf_header_inject_deep"]
            }
        },
        HC(),
    )
    names = [n for n, _ in vs._feature_testers]
    assert "crlf_header_inject_deep" in names
