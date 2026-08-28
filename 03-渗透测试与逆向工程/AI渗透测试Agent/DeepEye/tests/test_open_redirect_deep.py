"""Tests for OpenRedirectDeepTester."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pytest

from modules.open_redirect_deep.tester import OpenRedirectDeepTester, _REDIRECT_PARAMS, _PAYLOADS


class _FakeResponse:
    def __init__(self, status_code=200, headers=None, text=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text


class _FakeClient:
    def __init__(self, response):
        self._response = response

    def get(self, url, allow_redirects=False):
        return self._response


def _make_tester(status_code=200, headers=None, text=""):
    resp = _FakeResponse(status_code, headers or {}, text)
    return OpenRedirectDeepTester(_FakeClient(resp), {})


def test_no_query_params_returns_empty():
    t = _make_tester()
    assert t.scan("https://example.com/path") == []


def test_no_redirect_params_returns_empty():
    t = _make_tester()
    assert t.scan("https://example.com/path?foo=bar") == []


def test_3xx_location_evil_domain_detected():
    t = _make_tester(
        status_code=302,
        headers={"Location": "https://evil.example/callback"},
    )
    vulns = t.scan("https://example.com/login?redirect=https%3A%2F%2Fexample.com")
    assert len(vulns) == len(_PAYLOADS)
    for v in vulns:
        assert v["type"] == "Open Redirect (Deep)"
        assert v["severity"] == "medium"
        assert v["parameter"] == "redirect"
        assert "evil.example" in v["evidence"]


def test_javascript_scheme_in_location_detected():
    t = _make_tester(
        status_code=200,
        headers={"Location": "javascript:alert(1)"},
    )
    vulns = t.scan("https://example.com/login?redirect=https%3A%2F%2Fexample.com")
    assert len(vulns) == len(_PAYLOADS)
    for v in vulns:
        assert "Client-side Scheme" in v["type"]
        assert v["severity"] == "high"


def test_data_scheme_in_location_detected():
    t = _make_tester(
        status_code=200,
        headers={"Location": "data:text/html,<script>alert(1)</script>"},
    )
    vulns = t.scan("https://example.com/login?redirect=https%3A%2F%2Fexample.com")
    assert len(vulns) == len(_PAYLOADS)
    for v in vulns:
        assert "Client-side Scheme" in v["type"]
        assert v["severity"] == "high"


def test_meta_refresh_evil_domain_detected():
    t = _make_tester(
        text='<meta http-equiv="refresh" content="0;url=https://evil.example/x">',
    )
    vulns = t.scan("https://example.com/login?redirect=https%3A%2F%2Fexample.com")
    assert len(vulns) == len(_PAYLOADS)
    for v in vulns:
        assert "Meta Refresh" in v["type"]
        assert "evil.example" in v["evidence"]


def test_body_location_evil_domain_detected():
    t = _make_tester(
        text='<script>location="https://evil.example/x"</script>',
    )
    vulns = t.scan("https://example.com/login?redirect=https%3A%2F%2Fexample.com")
    assert len(vulns) == len(_PAYLOADS)
    for v in vulns:
        assert "Body Location" in v["type"]
        assert "evil.example" in v["evidence"]


def test_safe_response_returns_empty():
    t = _make_tester(
        status_code=302,
        headers={"Location": "https://example.com/safe"},
    )
    vulns = t.scan("https://example.com/login?redirect=https%3A%2F%2Fexample.com")
    assert vulns == []


def test_all_redirect_params_are_injected():
    """Ensure every known redirect param name triggers a probe when present."""
    for param in _REDIRECT_PARAMS:
        t = _make_tester(
            status_code=302,
            headers={"Location": "https://evil.example/x"},
        )
        url = f"https://example.com/login?{param}=https%3A%2F%2Fexample.com"
        vulns = t.scan(url)
        assert len(vulns) == len(_PAYLOADS), f"param={param} failed"


def test_http_error_handled_gracefully():
    class BadClient:
        def get(self, url, allow_redirects=False):
            raise RuntimeError("network error")

    t = OpenRedirectDeepTester(BadClient(), {})
    vulns = t.scan("https://example.com/login?redirect=https%3A%2F%2Fexample.com")
    assert vulns == []


def test_none_response_handled_gracefully():
    class NoneClient:
        def get(self, url, allow_redirects=False):
            return None

    t = OpenRedirectDeepTester(NoneClient(), {})
    vulns = t.scan("https://example.com/login?redirect=https%3A%2F%2Fexample.com")
    assert vulns == []
