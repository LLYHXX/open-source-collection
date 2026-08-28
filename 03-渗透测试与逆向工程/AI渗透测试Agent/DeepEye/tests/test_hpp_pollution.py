"""Tests for HPPTester."""
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from modules.hpp_pollution import HPPTester


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


class FakeHTTPClient:
    def __init__(self, responses, post_responses=None):
        """responses: dict mapping exact query strings to FakeResponse."""
        self._responses = responses
        self._post_responses = post_responses or {}
        self._calls = []

    def get(self, url, headers=None):
        self._calls.append(("GET", url, headers))
        qs = urlparse(url).query
        return self._responses.get(qs, FakeResponse("default", 200))

    def post(self, url, data=None, headers=None):
        self._calls.append(("POST", url, headers, data))
        return self._post_responses.get(data, FakeResponse("default", 200))


def test_hpp_no_query_params():
    client = FakeHTTPClient({})
    t = HPPTester(client, {})
    assert t.scan("https://example.com/") == []


def test_hpp_pollution_detected():
    """Polluted response differs from both baseline and probe."""
    client = FakeHTTPClient(
        {
            "id=1": FakeResponse("user=alice", 200),
            "id=HPP_PROBE_42": FakeResponse("user=none", 200),
            "id=1&id=HPP_PROBE_42": FakeResponse("1HPP_PROBE_42", 200),
        }
    )
    t = HPPTester(client, {})
    vulns = t.scan("https://example.com/?id=1")
    assert len(vulns) == 1
    v = vulns[0]
    assert v["type"] == "HTTP Parameter Pollution"
    assert v["parameter"] == "id"
    assert "HPP_PROBE_42" in v["payload"]
    assert "concatenation" in v["evidence"]


def test_hpp_no_difference():
    """Polluted response same as baseline → no finding."""
    client = FakeHTTPClient(
        {
            "id=1": FakeResponse("user=alice", 200),
            "id=HPP_PROBE_42": FakeResponse("user=none", 200),
            "id=1&id=HPP_PROBE_42": FakeResponse("user=alice", 200),
        }
    )
    t = HPPTester(client, {})
    assert t.scan("https://example.com/?id=1") == []


def test_hpp_last_wins():
    """Polluted response same as probe → last-wins behavior."""
    client = FakeHTTPClient(
        {
            "id=1": FakeResponse("user=alice", 200),
            "id=HPP_PROBE_42": FakeResponse("user=none", 200),
            "id=1&id=HPP_PROBE_42": FakeResponse("user=none", 200),
        }
    )
    t = HPPTester(client, {})
    vulns = t.scan("https://example.com/?id=1")
    assert len(vulns) == 1
    assert "last-wins" in vulns[0]["evidence"]


def test_hpp_json_probe_detected():
    """JSON duplicate key reflected in response."""
    dup_payload = '{"name": "HPP_JSON_PROBE"}'
    client = FakeHTTPClient(
        {},
        post_responses={dup_payload: FakeResponse('{"name": "HPP_JSON_PROBE"}', 200)},
    )
    t = HPPTester(client, {"hpp_pollution": {"json_probe": True}})
    vulns = t.scan(
        "https://example.com/api",
        {"content_type": "application/json", "body": '{"name": "alice"}'},
    )
    assert any(v["type"] == "HTTP Parameter Pollution (JSON duplicate key)" for v in vulns)


def test_hpp_json_probe_disabled():
    """JSON probe skipped when disabled."""
    client = FakeHTTPClient({})
    t = HPPTester(client, {"hpp_pollution": {"json_probe": False}})
    assert (
        t.scan(
            "https://example.com/api",
            {"content_type": "application/json", "body": '{"name": "alice"}'},
        )
        == []
    )


def test_hpp_max_params_respected():
    """Only first N parameters are probed."""
    calls = []

    class CountingClient:
        def get(self, url, headers=None):
            calls.append(url)
            return FakeResponse("ok", 200)

    t = HPPTester(CountingClient(), {"hpp_pollution": {"max_params": 2}})
    t.scan("https://example.com/?a=1&b=2&c=3&d=4")
    # baseline + 2 params * (probe + polluted) = 1 + 4 = 5 GETs
    assert len(calls) == 5
