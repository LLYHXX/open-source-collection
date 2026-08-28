# Scan Flow

## Entry

```bash
python deep_eye.py -u https://target.com [--scope-nl "..."] [--retest-new baseline.json]
```

`deep_eye.py:main()`:

1. Parse args  
2. Load config (or onboard wizard)  
3. Apply `--scope-nl` if set  
4. Build `AIProviderManager` + `ScannerEngine`  
5. `scanner.scan(...)`  
6. Optional `--retest-new` filter on results  
7. `ReportGenerator` for each format  
8. Notifications (if enabled)

## Phase diagram

```
INITIALIZATION
  HTTPClient, modules, plugins, OAST?, proxy?, templates?, auth_session?
       │
       ▼
LOGIN REPLAY (optional) ── login_replay.enabled + macro
       │
       ▼
RECONNAISSANCE (optional) ── enable_recon / ReconEngine
       │
       ▼
SUBDOMAIN DISCOVERY (optional) ── experimental.enable_subdomain_scanning
       │
       ▼
CRAWLING ── ThreadPoolExecutor BFS
  + OpenAPI seed (openapi.enabled → expand endpoints into URL set)
  + AI planner (ai_planner.enabled → threads / max_urls / check order hint)
       │
       ▼
VULNERABILITY SCANNING (per URL, parallel)
  1. Scope / filter skip
  2. GET response
  3. challenge_solver.solve? 
  4. captcha detect → skip if protected
  5. AIPayloadGenerator.generate_payloads
  6. VulnerabilityScanner.scan
       - built-in _check_*
       - classic modules (api, auth, …)
       - _feature_testers (cors_csp, jwt_deep, idor, …)
  7. Browser automation (advanced.enable_javascript_rendering)
  8. Plugins
  9. YAML templates (templates.enabled)
 10. Extra modules (directory_bruteforce, port_scanner, …)
 11. SecretsDetector (+ SecretScanner content)
 12. CVEMatcher enrich (experimental)
       │
       ▼
POST-SCAN
  1. Dedupe (reporting.dedupe / finding_fingerprint)
  2. FP replay (fp_replay.enabled)
  3. Evidence summary (evidence_summary.enabled)
  4. RAG CVE link (rag.enabled)
  5. Compliance frameworks (compliance.enabled)
  6. AI triage + bounty writer (ai_triage / bug_bounty)
       │
       ▼
REPORTING + NOTIFICATIONS + checkpoint save
```

## Diff-only mode

```bash
python deep_eye.py --diff baseline.json current.json --diff-format html
```

Skips scan; uses `core/scan_diff.py` + `utils/exports/diff_renderer.py`.

## Retest-new mode

After a normal scan, `--retest-new baseline.json` keeps only findings whose identity `(type, url, parameter)` is not in the baseline. Useful for CI “what’s new since last run”.

## Result shape

Each finding is a dict:

```python
{
  "type": str,
  "severity": "critical|high|medium|low|info",
  "url": str,
  "parameter": str,      # optional
  "payload": str,        # optional
  "evidence": str,
  "remediation": str,
  "fingerprint": str,    # optional, set by dedupe
  "cve_references": [],  # optional
  "ai_evidence_summary": str,  # optional
  "false_positive": bool,      # optional (triage)
}
```

## Threading

- Crawl: `ThreadPoolExecutor(max_workers=min(threads, 10))`
- Scan: `ThreadPoolExecutor(max_workers=threads)` (1–50)
- Shared `HTTPClient` + lock on `vulnerabilities` list

## Related docs

- [ARCHITECTURE.md](ARCHITECTURE.md)  
- [CONFIGURATION.md](CONFIGURATION.md)  
- [MODULES.md](MODULES.md)  
