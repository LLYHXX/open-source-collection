"""Live CVE lookup + link enrichment tests (mocked HTTP)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_attach_reference_links():
    from modules.cve_intelligence.live_lookup import attach_reference_links

    links = attach_reference_links("CVE-2021-44228")
    assert "nvd.nist.gov" in links["nvd"]
    assert "exploit-db.com" in links["exploit_db"]
    assert "github.com/search" in links["github_poc"]


def test_keyword_from_finding_prefers_cve_id():
    from modules.cve_intelligence.live_lookup import keyword_from_finding

    kw = keyword_from_finding(
        {
            "type": "RCE",
            "evidence": "see CVE-2021-44228 in logs",
            "description": "log4j",
        }
    )
    assert kw == "CVE-2021-44228"


def test_nvd_search_keyword_mocked():
    from modules.cve_intelligence import live_lookup

    live_lookup._cache.clear()
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2024-0001",
                    "descriptions": [{"lang": "en", "value": "SQL injection in foo"}],
                    "metrics": {
                        "cvssMetricV31": [
                            {
                                "cvssData": {
                                    "baseScore": 9.8,
                                    "baseSeverity": "CRITICAL",
                                    "vectorString": "CVSS:3.1/AV:N",
                                }
                            }
                        ]
                    },
                    "published": "2024-01-01T00:00:00.000",
                    "references": [{"url": "https://example.com/advisory"}],
                }
            }
        ]
    }
    session.get.return_value = resp
    hits = live_lookup.nvd_search_keyword("sql injection", max_results=3, session=session)
    assert hits and hits[0]["cve_id"] == "CVE-2024-0001"
    assert hits[0]["cvss_score"] == 9.8
    assert hits[0]["links"]["nvd"]


def test_enrich_adds_links_from_local_db(tmp_path):
    from modules.cve_intelligence.cve_matcher import CVEMatcher

    db = tmp_path / "cve.db"
    m = CVEMatcher(str(db))
    m.ensure_seed_if_empty(min_rows=5)
    m.live_config = {"enabled": False}
    out = m.enrich_vulnerability(
        {
            "type": "SQL Injection",
            "url": "https://x",
            "evidence": "mysql",
            "remediation": "prep",
        }
    )
    assert out.get("cve_matched")
    assert out.get("related_cves")
    assert out["related_cves"][0].get("links", {}).get("nvd")
    assert out.get("cve_links")


def test_live_enrich_with_mocks(tmp_path, monkeypatch):
    from modules.cve_intelligence.cve_matcher import CVEMatcher
    from modules.cve_intelligence import live_lookup

    live_lookup._cache.clear()
    db = tmp_path / "cve.db"
    m = CVEMatcher(str(db))
    m.ensure_seed_if_empty(min_rows=5)
    m.live_config = {
        "enabled": True,
        "nvd_api_key": "",
        "github_token": "",
        "max_results": 2,
        "keyword_search": True,
        "github_search": True,
        "fetch_cve_detail": False,
        "always_keyword_search": True,
    }

    monkeypatch.setattr(
        live_lookup,
        "nvd_search_keyword",
        lambda *a, **k: [
            {
                "cve_id": "CVE-2099-9999",
                "description": "test live",
                "severity": "HIGH",
                "cvss_score": 8.0,
                "links": live_lookup.attach_reference_links("CVE-2099-9999"),
            }
        ],
    )
    monkeypatch.setattr(
        live_lookup,
        "github_search_repos",
        lambda *a, **k: [
            {
                "full_name": "org/poc",
                "stars": 10,
                "url": "https://github.com/org/poc",
                "description": "poc",
                "language": "Python",
            }
        ],
    )

    out = m.enrich_vulnerability(
        {"type": "SQL Injection", "url": "https://x", "evidence": "err"}
    )
    assert out.get("cve_matched")
    ids = [r.get("cve_id") for r in out.get("related_cves") or []]
    assert "CVE-2099-9999" in ids
    assert out.get("cve_github_pocs")


def test_get_cve_matcher_wires_live_config(tmp_path):
    from modules.cve_intelligence.cve_matcher import get_cve_matcher

    db = tmp_path / "cve.db"
    m = get_cve_matcher(
        {
            "experimental": {
                "enable_cve_matching": True,
                "cve_database_path": str(db),
                "cve_live_lookup": True,
                "nvd_api_key": "k",
            }
        },
        auto_seed=True,
    )
    assert m is not None
    assert m.live_config.get("enabled") is True
    assert m.live_config.get("nvd_api_key") == "k"
