"""Tests for host_header_deep module."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from modules.host_header_deep import HostHeaderDeepTester


class R:
    def __init__(self, text="", headers=None, status_code=200):
        self.text = text
        self.headers = headers or {}
        self.status_code = status_code


class HC:
    def __init__(self, response_map=None):
        self._map = response_map or {}

    def get(self, url, headers=None):
        key = tuple(sorted((headers or {}).items()))
        return self._map.get(key, R())


def _make_map(reflect_header, reflect_value, body="", extra_headers=None):
    h = {reflect_header: reflect_value}
    if extra_headers:
        h.update(extra_headers)
    return {
        tuple(sorted(h.items())): R(text=body, headers=extra_headers or {}),
    }


def test_host_reflected_in_body():
    body = "<a href=\"http://evil-poison.example/reset\">Click</a>"
    hc = HC(_make_map("Host", "evil-poison.example", body=body))
    t = HostHeaderDeepTester(hc, {})
    vulns = t.scan("https://target.com/page")
    assert any(v["type"] == "Host Header Injection (Host)" and v["severity"] == "medium" for v in vulns)


def test_x_forwarded_host_reflected_in_headers():
    hc = HC(
        {
            tuple(sorted({"X-Forwarded-Host": "evil-poison.example"}.items())): R(
                headers={"Location": "http://evil-poison.example/login"}
            ),
        }
    )
    t = HostHeaderDeepTester(hc, {})
    vulns = t.scan("https://target.com/page")
    assert any(
        v["type"] == "Host Header Injection (X-Forwarded-Host)" and v["severity"] == "medium"
        for v in vulns
    )


def test_password_reset_path_high_severity():
    body = "Check your email at evil-poison.example"
    hc = HC(_make_map("Host", "evil-poison.example", body=body))
    t = HostHeaderDeepTester(hc, {})
    vulns = t.scan("https://target.com/forgot-password")
    assert any(v["severity"] == "high" for v in vulns)


def test_no_reflection_no_finding():
    hc = HC({tuple(sorted({"Host": "evil-poison.example"}.items())): R(text="ok")})
    t = HostHeaderDeepTester(hc, {})
    vulns = t.scan("https://target.com/page")
    assert len(vulns) == 0


def test_userinfo_confusion_reflected():
    body = "evil-poison.example@target.com is not allowed"
    hc = HC(
        {
            tuple(
                sorted({"Host": "evil-poison.example@target.com"}.items())
            ): R(text=body),
        }
    )
    t = HostHeaderDeepTester(hc, {})
    vulns = t.scan("https://target.com/page")
    assert any(v["type"] == "Host userinfo confusion" for v in vulns)


def test_forwarded_header_reflected():
    body = "Forwarded host evil-poison.example processed"
    hc = HC(
        {
            tuple(sorted({"Forwarded": "host=evil-poison.example"}.items())): R(text=body),
        }
    )
    t = HostHeaderDeepTester(hc, {})
    vulns = t.scan("https://target.com/page")
    assert any(v["type"] == "Host Header Injection (Forwarded)" for v in vulns)


def test_absolute_url_confusion_reflected():
    body = "Redirecting to https://evil-poison.example/page"
    hc = HC(
        {
            tuple(
                sorted({"X-Original-URL": "https://evil-poison.example/page"}.items())
            ): R(text=body),
        }
    )
    t = HostHeaderDeepTester(hc, {})
    vulns = t.scan("https://target.com/page")
    assert any("Absolute-URL host confusion" in v["type"] for v in vulns)


def test_multiple_findings_different_headers():
    body = "evil-poison.example"
    hc = HC(
        {
            tuple(sorted({"Host": "evil-poison.example"}.items())): R(text=body),
            tuple(sorted({"X-Forwarded-Host": "evil-poison.example"}.items())): R(text=body),
        }
    )
    t = HostHeaderDeepTester(hc, {})
    vulns = t.scan("https://target.com/page")
    types = {v["type"] for v in vulns}
    assert "Host Header Injection (Host)" in types
    assert "Host Header Injection (X-Forwarded-Host)" in types


def test_vuln_has_standard_keys():
    body = "evil-poison.example"
    hc = HC(_make_map("Host", "evil-poison.example", body=body))
    t = HostHeaderDeepTester(hc, {})
    vulns = t.scan("https://target.com/page")
    assert len(vulns) > 0
    v = vulns[0]
    for key in ("type", "severity", "url", "parameter", "payload", "evidence", "description", "remediation"):
        assert key in v, f"missing key {key}"
