# CVE INTELLIGENCE MODULE

## OVERVIEW
CVE intelligence pipeline. Fetches CVE data, matches findings to known vulnerabilities, optional RAG enrichment via ChromaDB. SQLite for storage, ChromaDB for vector search.

## STRUCTURE
- `cve_scraper.py` (~1725 LOC): NVD/API scraper. Populates `data/cve_intelligence.db`.
- `cve_matcher.py`: Matches scan findings to CVE records by keyword/version.
- `rag_index.py`: `CVERagIndex` class. ChromaDB vector search over CVE descriptions.
- Build scripts (repo root, not this package): `scripts/update_cve_database.py`, `scripts/build_cve_rag_index.py`
- `data/cve_intelligence.db`: SQLite store (gitignored).

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add CVE source | `cve_scraper.py` | Hotspot; prefer new helper module over inline growth |
| Matching logic | `cve_matcher.py` | Called by `ScannerEngine` if `enable_cve_matching` |
| Vector search | `rag_index.py` | `CVERagIndex(config)`; `search(query, n_results)` |
| Refresh DB | `scripts/update_cve_database.py` | Idempotent; safe to rerun |
| Rebuild index | `scripts/build_cve_rag_index.py` | Idempotent |
| Integration | `core/scanner_engine.py` | CVEMatcher enrich, then RAG if `rag.enabled` |
| Tests | `tests/test_rag_index.py` | Covers `CVERagIndex` only |

## CONVENTIONS
- Gated by `experimental.enable_cve_matching` in config.
- Config keys: `experimental.cve_database_path`, `cve_intelligence.database_path`, `rag.*`, `payload_generation.cve_database`.
- Live lookup (optional): `experimental.cve_live_lookup` + NVD/GitHub tokens — original Deep Eye code in `live_lookup.py` using public NIST NVD 2.0 + GitHub Search APIs.
- Live lookup attaches `links` (NVD, Exploit-DB search, GitHub POC search), optional `cve_github_pocs`, and can keyword-search NVD when local DB is thin.
- Do **not** vendor or import third-party tools that forbid integration (e.g. exploit-eye license).
- Use `get_cve_matcher(config, auto_seed=True)` — seeds minimal CVEs if DB empty/missing.
- `enrich_vulnerability` sets `related_cves`, `cve_references`, `cve_matched`, `cve_links`.
- Severity UNKNOWN treated as LOW so sparse scrapes still match.
- `CVERagIndex` separate post-scan path (`rag.enabled`).

## ENABLE
```yaml
experimental:
  enable_cve_matching: true
  cve_database_path: "data/cve_intelligence.db"
  cve_live_lookup: true          # optional online NVD/GitHub refs
  nvd_api_key: ""                # optional NIST key
  github_token: ""
vulnerability_scanner:
  payload_generation:
    cve_database: true
```
```bash
python scripts/update_cve_database.py   # full refresh
pytest tests/test_cve_matching.py tests/test_cve_live_lookup.py -v
```

## NOTES
- `cve_technologies` may be empty after scrape; matcher also searches description/product/vendor.
- Seed pack ships high-signal CVEs (Log4Shell, Struts, Shellshock, jQuery XSS, etc.) when DB < 5 rows.
- Tests: `tests/test_cve_matching.py`, `tests/test_cve_live_lookup.py`.
- `live_lookup.py` is Deep Eye original; public API clients only.
