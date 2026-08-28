"""API / WebSocket / SSE / cloud / PHP module tests."""
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


def test_api_bola_id_swap():
    from modules.api_bola_deep import APIBolaDeepTester

    class HC:
        def get(self, url, headers=None):
            if "/users/2" in url:
                return R(200, '{"id":2,"name":"other"}')
            return R(200, '{"id":1,"name":"me"}')

        def post(self, url, json=None, headers=None, data=None):
            return R(200, '{"ok":true,"role":"admin"}')

    t = APIBolaDeepTester(HC(), {"api_bola_deep": {"force": True}})
    vulns = t.scan("https://api.example.com/api/users/1")
    assert any("BOLA" in v.get("type", "") or "Mass Assignment" in v.get("type", "") for v in vulns)


def test_websocket_deep_upgrade():
    from modules.websocket_deep import WebSocketDeepTester

    class HC:
        def get(self, url, headers=None):
            return R(101, "", {"Upgrade": "websocket"})

    t = WebSocketDeepTester(HC(), {})
    vulns = t.scan("https://example.com/")
    assert any("WebSocket" in v.get("type", "") for v in vulns)


def test_sse_endpoint():
    from modules.sse_injection import SSEInjectionTester

    class HC:
        def get(self, url, headers=None):
            return R(200, "data: hello\n\n", {"Content-Type": "text/event-stream"})

    t = SSEInjectionTester(HC(), {})
    vulns = t.scan("https://example.com/")
    assert any("SSE" in v.get("type", "") for v in vulns)


def test_cloud_bucket_listing():
    from modules.cloud_misconfig import CloudMisconfigTester

    class HC:
        def get(self, url, headers=None):
            if "s3.amazonaws.com" in url:
                return R(200, "<?xml><ListBucketResult><Contents><Key>a</Key></Contents></ListBucketResult>")
            return R(404, "Not Found")

    t = CloudMisconfigTester(HC(), {"cloud_misconfig": {"probe_metadata_via_ssrf_params": False}})
    vulns = t.scan("https://mybucket.example.com/")
    assert any("Bucket" in v.get("type", "") for v in vulns)


def test_php_webshell_lfi():
    from modules.php_webshell import PHPWebshellLFITester
    from urllib.parse import unquote

    class HC:
        def get(self, url, headers=None):
            u = unquote(url)
            if "php://filter" in u or "etc/passwd" in u or "php%3A" in url:
                return R(200, "root:x:0:0:root:/root:/bin/bash")
            return R(200, "ok")

        def post(self, url, data=None, headers=None, json=None):
            return R(200, "ok")

    t = PHPWebshellLFITester(HC(), {"php_webshell": {"force": True}})
    vulns = t.scan("https://x.com/index.php?page=home", {"headers": {"X-Powered-By": "PHP/8.1"}})
    assert any("PHP" in v.get("type", "") or "LFI" in v.get("type", "") for v in vulns)
