"""Enhanced idor / ssrf_cloud / stored_xss / email / graphql tests."""
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


def test_idor_uuid_and_int():
    from modules.idor import IDORTester

    class HC:
        def get(self, url, headers=None):
            if "/users/2" in url or "999" in url:
                return R(200, "other user profile data " + "x" * 80)
            return R(200, "me short")

    t = IDORTester(HC(), {"idor": {"max_swaps": 10}})
    vulns = t.scan("https://api.example.com/users/1")
    assert any("IDOR" in v.get("type", "") for v in vulns)


def test_ssrf_cloud_metadata():
    from modules.ssrf_cloud import SSRFCloudTester

    class HC:
        def get(self, url, headers=None):
            if "169.254" in url or "meta-data" in url:
                return R(200, "ami-id\ninstance-id\ni-123")
            return R(200, "ok")

    t = SSRFCloudTester(HC(), {})
    vulns = t.scan("https://x.com/fetch?url=http://example.com")
    assert any("SSRF" in v.get("type", "") for v in vulns)


def test_stored_xss_marker():
    from modules.stored_xss import StoredXSSTester

    store = {"body": ""}

    class HC:
        def get(self, url, headers=None):
            return R(200, store["body"] or "empty")

        def post(self, url, data=None, json=None, headers=None):
            blob = str(data or json or "")
            if "deepeye_sxss_" in blob or "onerror" in blob:
                store["body"] = blob + " rendered"
            return R(200, "ok")

    t = StoredXSSTester(HC(), {})
    vulns = t.scan("https://x.com/comment")
    assert any("Stored XSS" in v.get("type", "") for v in vulns)


def test_email_injection_accept():
    from modules.email_injection import EmailHeaderInjectionTester

    class HC:
        def post(self, url, data=None, json=None, headers=None):
            return R(200, "thanks for contacting us")

    t = EmailHeaderInjectionTester(HC(), {})
    vulns = t.scan("https://x.com/contact", {"response": R(200, "email form")})
    assert any("Email" in v.get("type", "") for v in vulns)


def test_graphql_introspection_and_variables():
    from modules.graphql_deep import GraphQLDeepTester

    class HC:
        def post(self, url, json=None, headers=None):
            body = json or {}
            q = body.get("query") if isinstance(body, dict) else ""
            if isinstance(body, list):
                return R(200, '{"data":{"__typename":"Q"}}' * 20)
            if isinstance(q, str) and "__schema" in q:
                return R(200, '{"data":{"__schema":{"queryType":{"name":"Query"},"types":[]}}}')
            if isinstance(body, dict) and body.get("variables"):
                return R(200, 'SQL syntax error near OR 1=1')
            if isinstance(q, str) and "__typenamee" in q:
                return R(400, 'Cannot query field "__typenamee". Did you mean "__typename"?')
            return R(200, '{"data":{"__typename":"Query"}}')

    t = GraphQLDeepTester(HC(), {})
    vulns = t.scan("https://x.com/graphql")
    types = " ".join(v.get("type", "") for v in vulns)
    assert "Introspection" in types or "Variables" in types or "Suggestion" in types or "Batch" in types
