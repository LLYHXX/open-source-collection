"""Tests for SSTIEnginesTester."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


class _Resp:
    def __init__(self, text: str = "", status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.headers = {}


class _HC:
    def __init__(self, resp):
        self._resp = resp

    def get(self, url, headers=None):
        return self._resp


def test_no_query_params_returns_empty():
    from modules.ssti_engines import SSTIEnginesTester

    t = SSTIEnginesTester(_HC(_Resp()), {})
    assert t.scan("https://example.com/path") == []


def test_jinja_math_evaluated():
    from modules.ssti_engines import SSTIEnginesTester

    resp = _Resp(text="result: 49 end")
    t = SSTIEnginesTester(_HC(resp), {})
    vulns = t.scan("https://example.com/page?q=1")
    assert len(vulns) == 1
    assert "Jinja" in vulns[0]["type"] or "Jinja2" in vulns[0]["type"]
    assert vulns[0]["severity"] == "critical"
    assert vulns[0]["parameter"] == "q"
    assert "49" in vulns[0]["evidence"]


def test_spel_runtime_detected():
    from modules.ssti_engines import SSTIEnginesTester

    resp = _Resp(text="java.lang.Runtime@abc123")
    t = SSTIEnginesTester(_HC(resp), {})
    vulns = t.scan("https://example.com/page?q=1")
    assert len(vulns) == 1
    assert "SpEL" in vulns[0]["type"]
    assert vulns[0]["severity"] == "critical"


def test_literal_echo_avoids_false_positive():
    from modules.ssti_engines import SSTIEnginesTester

    # Server echoes the literal payload back without evaluating it
    resp = _Resp(text="{{7*7}}")
    t = SSTIEnginesTester(_HC(resp), {})
    vulns = t.scan("https://example.com/page?q=1")
    assert vulns == []


def test_deep_eval_7777777():
    from modules.ssti_engines import SSTIEnginesTester

    resp = _Resp(text="7777777")
    t = SSTIEnginesTester(_HC(resp), {})
    vulns = t.scan("https://example.com/page?q=1")
    assert len(vulns) == 1
    assert "deep eval" in vulns[0]["type"]
    assert vulns[0]["severity"] == "critical"


def test_scanner_registers_feature_tester():
    from core.vulnerability_scanner import VulnerabilityScanner

    class HC:
        def get(self, *a, **k):
            return None

    vs = VulnerabilityScanner(
        {
            "vulnerability_scanner": {
                "enabled_checks": ["ssti_engines"]
            }
        },
        HC(),
    )
    names = [n for n, _ in vs._feature_testers]
    assert "ssti_engines" in names
