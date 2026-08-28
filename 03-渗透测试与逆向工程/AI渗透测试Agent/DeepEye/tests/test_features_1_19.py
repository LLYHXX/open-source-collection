"""Tests for features 1-19 infra + modules."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_fingerprint_dedupe():
    from utils.finding_fingerprint import fingerprint, dedupe_findings

    a = {
        "type": "XSS",
        "url": "https://x.com/a?q=1",
        "parameter": "q",
        "severity": "low",
        "evidence": "e1",
        "payload": "p",
    }
    b = {
        "type": "XSS",
        "url": "https://x.com/a?q=1",
        "parameter": "q",
        "severity": "high",
        "evidence": "e1",
        "payload": "p",
    }
    assert fingerprint(a) == fingerprint(b)
    out = dedupe_findings([a, b])
    assert len(out) == 1
    assert out[0]["severity"] == "high"
    assert "fingerprint" in out[0]


def test_nl_scope_parse():
    from utils.nl_scope import parse_nl_scope, apply_nl_scope_to_config

    p = parse_nl_scope("only /api/* no /logout host target.com ports 80,443")
    assert p["enabled"]
    assert "target.com" in p["allowed_hosts"]
    assert any("logout" in x for x in p["excluded_paths"])
    assert 80 in p["allowed_ports"]
    assert "/api/*" in p["path_allow"]
    cfg = apply_nl_scope_to_config({}, "only /api/* host *.example.com")
    assert cfg["scope"]["enabled"]


def test_openapi_expand():
    from modules.openapi_ingest.parser import expand_endpoints

    spec = {
        "openapi": "3.0.0",
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/users/{id}": {
                "get": {
                    "parameters": [
                        {"name": "id", "in": "path", "schema": {"type": "integer"}}
                    ],
                    "tags": ["users"],
                }
            }
        },
    }
    eps = expand_endpoints(spec)
    assert len(eps) == 1
    assert "users" in eps[0]["url"]
    assert eps[0]["method"] == "GET"


def test_cors_csp_missing_csp():
    from modules.cors_csp import CorsCspTester

    class R:
        status_code = 200
        headers = {}
        text = "ok"

    class HC:
        def get(self, url, headers=None):
            return R()

    t = CorsCspTester(HC(), {})
    vulns = t.scan("https://example.com/")
    assert any(v["type"] == "Missing Content-Security-Policy" for v in vulns)


def test_jwt_alg_none_builder():
    from modules.jwt_deep.tester import _make_token

    tok = _make_token({"alg": "none", "typ": "JWT"}, {"sub": "1"}, b"")
    assert tok.startswith("eyJ")
    assert tok.count(".") == 2


def test_ai_planner_heuristic():
    from modules.ai_planner import AIAttackPlanner

    p = AIAttackPlanner(None, {"ai_planner": {"enabled": True, "use_ai": False}})
    plan = p.plan(
        recon_data={"technologies": ["graphql", "jwt"]},
        enabled_checks=["graphql_deep", "jwt_deep", "xss"],
    )
    assert plan["order"][0] in ("graphql_deep", "jwt_deep")
    assert "xss" in plan["order"]


def test_supply_chain_missing_sri():
    from modules.supply_chain_js import SupplyChainJSTester

    class R:
        text = (
            '<script src="https://cdn.example.com/jquery-1.12.4.min.js"></script>'
        )
        headers = {}

    class HC:
        def get(self, url, headers=None):
            return R()

    t = SupplyChainJSTester(HC(), {})
    vulns = t.scan("https://app.example.com/", {"response": R()})
    assert any("SRI" in v["type"] or "Outdated" in v["type"] for v in vulns)


def test_scope_path_allow():
    from utils.scope_manager import ScopeManager

    sm = ScopeManager(
        {
            "scope": {
                "enabled": True,
                "allowed_hosts": ["example.com"],
                "allowed_ports": [443],
                "excluded_paths": [],
                "path_allow": ["/api/*"],
            }
        }
    )
    assert sm.is_in_scope("https://example.com/api/v1")
    assert not sm.is_in_scope("https://example.com/admin")


def test_feature_testers_load_on_scanner():
    from core.vulnerability_scanner import VulnerabilityScanner

    class HC:
        def get(self, *a, **k):
            return None

        def post(self, *a, **k):
            return None

    vs = VulnerabilityScanner(
        {
            "vulnerability_scanner": {
                "enabled_checks": ["cors_csp", "waf_fingerprint"]
            }
        },
        HC(),
    )
    names = [n for n, _ in vs._feature_testers]
    assert "cors_csp" in names
    assert "waf_fingerprint" in names
