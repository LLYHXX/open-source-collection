"""Tests for HTTPMethodOverrideTester."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from modules.http_method_override import HTTPMethodOverrideTester


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


class FakeHTTPClient:
    def __init__(self, method_map):
        """method_map: dict of (method, url, header_keys_tuple) -> FakeResponse."""
        self._map = method_map
        self._calls = []

    def _lookup(self, method, url, headers):
        key = (method, url, tuple(sorted(headers.keys())) if headers else ())
        if key in self._map:
            return self._map[key]
        # Any request with an override header that is not explicitly mapped
        # should be treated as blocked (405) by default.
        if headers and any(
            h in headers for h in ("X-HTTP-Method-Override", "X-HTTP-Method", "X-METHOD-OVERRIDE", "_method")
        ):
            return FakeResponse(405)
        return FakeResponse(200)

    def get(self, url, headers=None):
        self._calls.append(("GET", url, headers))
        return self._lookup("GET", url, headers)

    def post(self, url, data=None, headers=None):
        self._calls.append(("POST", url, headers))
        return self._lookup("POST", url, headers)

    def delete(self, url, headers=None):
        self._calls.append(("DELETE", url, headers))
        return self._lookup("DELETE", url, headers)

    def put(self, url, data=None, headers=None):
        self._calls.append(("PUT", url, headers))
        return self._lookup("PUT", url, headers)

    def patch(self, url, data=None, headers=None):
        self._calls.append(("PATCH", url, headers))
        return self._lookup("PATCH", url, headers)

    def request(self, method, url, headers=None):
        self._calls.append((method, url, headers))
        return FakeResponse(200)


def test_override_bypass_detected():
    """Real DELETE blocked, override via GET returns 200."""
    url = "https://example.com/api/users/1"
    client = FakeHTTPClient(
        {
            ("DELETE", url, ()): FakeResponse(405),
            ("GET", url, ("X-HTTP-Method-Override",)): FakeResponse(200),
        }
    )
    t = HTTPMethodOverrideTester(client, {})
    vulns = t.scan(url)
    assert len(vulns) == 1
    v = vulns[0]
    assert v["type"] == "HTTP Method Override Bypass"
    assert v["severity"] == "high"
    assert "DELETE" in v["payload"]
    assert "405" in v["evidence"]
    assert "200" in v["evidence"]


def test_override_no_bypass_when_real_works():
    """If real DELETE already returns 200, no bypass to report."""
    url = "https://example.com/api/users/1"
    client = FakeHTTPClient(
        {
            ("DELETE", url, ()): FakeResponse(200),
        }
    )
    t = HTTPMethodOverrideTester(client, {})
    assert t.scan(url) == []


def test_override_no_bypass_when_override_blocked():
    """Real DELETE blocked, but override also blocked → no finding."""
    url = "https://example.com/api/users/1"
    client = FakeHTTPClient(
        {
            ("DELETE", url, ()): FakeResponse(405),
            ("GET", url, ("X-HTTP-Method-Override",)): FakeResponse(405),
            ("POST", url, ("X-HTTP-Method-Override",)): FakeResponse(405),
        }
    )
    t = HTTPMethodOverrideTester(client, {})
    assert t.scan(url) == []


def test_override_post_carrier():
    """Override via POST carrier also detected."""
    url = "https://example.com/api/users/1"
    client = FakeHTTPClient(
        {
            ("DELETE", url, ()): FakeResponse(405),
            ("GET", url, ("X-HTTP-Method-Override",)): FakeResponse(405),
            ("POST", url, ("X-HTTP-Method-Override",)): FakeResponse(204),
        }
    )
    t = HTTPMethodOverrideTester(client, {})
    vulns = t.scan(url)
    assert len(vulns) == 1
    assert "POST" in vulns[0]["payload"]
    assert "204" in vulns[0]["evidence"]


def test_override_multiple_headers():
    """Tests all override header variants."""
    url = "https://example.com/api/users/1"
    client = FakeHTTPClient(
        {
            ("DELETE", url, ()): FakeResponse(405),
            ("GET", url, ("X-HTTP-Method-Override",)): FakeResponse(405),
            ("GET", url, ("X-HTTP-Method",)): FakeResponse(405),
            ("GET", url, ("X-METHOD-OVERRIDE",)): FakeResponse(200),
        }
    )
    t = HTTPMethodOverrideTester(client, {})
    vulns = t.scan(url)
    assert len(vulns) == 1
    assert "X-METHOD-OVERRIDE" in vulns[0]["payload"]


def test_override_custom_methods():
    """Custom probe_methods config respected."""
    url = "https://example.com/api/users/1"
    client = FakeHTTPClient(
        {
            ("PATCH", url, ()): FakeResponse(405),
            ("GET", url, ("X-HTTP-Method-Override",)): FakeResponse(200),
        }
    )
    t = HTTPMethodOverrideTester(client, {"http_method_override": {"probe_methods": ["PATCH"]}})
    vulns = t.scan(url)
    assert len(vulns) == 1
    assert "PATCH" in vulns[0]["payload"]
