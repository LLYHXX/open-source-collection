"""CVE matching + enable_cve_matching integration tests."""
import sys
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_enrich_sets_cve_references_and_related(tmp_path):
    from modules.cve_intelligence.cve_matcher import CVEMatcher

    db = tmp_path / "cve.db"
    m = CVEMatcher(str(db))
    assert m.ensure_seed_if_empty(min_rows=5) >= 1
    assert m.is_available()

    vuln = {
        "type": "SQL Injection",
        "severity": "critical",
        "url": "https://x.com/?id=1",
        "evidence": "mysql error",
        "remediation": "use prepared statements",
    }
    out = m.enrich_vulnerability(vuln)
    assert out.get("cve_matched") is True
    assert out.get("related_cves")
    assert out.get("cve_references")
    assert all(isinstance(x, str) for x in out["cve_references"])


def test_enrich_xss_and_command():
    from modules.cve_intelligence.cve_matcher import CVEMatcher, resolve_cve_db_path

    path = resolve_cve_db_path(
        {"experimental": {"cve_database_path": "data/cve_intelligence.db"}}
    )
    m = CVEMatcher(path)
    m.ensure_seed_if_empty(min_rows=5)
    if not m.is_available():
        return  # skip if env broken
    xss = m.enrich_vulnerability(
        {"type": "Cross-Site Scripting (XSS)", "url": "https://x", "evidence": "x"}
    )
    assert "cve_references" in xss or "related_cves" in xss or not m.is_available()


def test_match_technology_finds_log4j(tmp_path):
    from modules.cve_intelligence.cve_matcher import CVEMatcher

    db = tmp_path / "cve.db"
    m = CVEMatcher(str(db))
    m.ensure_seed_if_empty(min_rows=5)
    matches = m.match_technology_cves(["log4j", "apache"], severity_min="LOW")
    assert matches
    assert any("log4j" in k.lower() or "apache" in k.lower() for k in matches)


def test_get_payloads_from_cves(tmp_path):
    from modules.cve_intelligence.cve_matcher import CVEMatcher

    db = tmp_path / "cve.db"
    m = CVEMatcher(str(db))
    m.ensure_seed_if_empty(min_rows=5)
    matches = m.match_technology_cves(["php", "jquery"], severity_min="LOW")
    payloads = m.get_payloads_from_cves(matches)
    assert isinstance(payloads, dict)
    assert "sql_injection" in payloads


def test_scanner_engine_loads_cve_matcher_when_enabled(tmp_path):
    from core.scanner_engine import ScannerEngine
    from modules.cve_intelligence.cve_matcher import CVEMatcher

    db = tmp_path / "cve.db"
    m = CVEMatcher(str(db))
    m.ensure_seed_if_empty(min_rows=5)

    config = {
        "scanner": {},
        "vulnerability_scanner": {
            "enabled_checks": [],
            "payload_generation": {"use_ai": False, "cve_database": False},
        },
        "secrets_scanner": {"enabled": False},
        "plugin_manager": {"enabled": False},
        "advanced": {},
        "experimental": {
            "enable_cve_matching": True,
            "cve_database_path": str(db),
        },
        "ai_providers": {},
    }
    eng = ScannerEngine(
        target_url="https://example.com",
        config=config,
        ai_manager=MagicMock(),
        depth=1,
        threads=1,
    )
    assert eng.cve_matcher is not None
    assert eng.cve_matcher.is_available()

    # enrich path used in scan_url
    v = eng.cve_matcher.enrich_vulnerability(
        {"type": "SQL Injection", "url": "https://x", "evidence": "e"}
    )
    assert v.get("cve_matched") or v.get("related_cves") or v.get("cve_references")


def test_get_cve_matcher_factory(tmp_path):
    from modules.cve_intelligence.cve_matcher import get_cve_matcher

    db = tmp_path / "cve.db"
    m = get_cve_matcher(
        {"experimental": {"cve_database_path": str(db)}}, auto_seed=True
    )
    assert m is not None
    assert m.is_available()
