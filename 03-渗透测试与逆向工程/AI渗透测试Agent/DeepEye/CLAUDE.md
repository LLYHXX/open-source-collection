# CLAUDE.md

Guidance for AI agents working in this repository.

## Overview

Deep Eye is an AI-driven penetration testing tool. Multi-provider payload generation → crawl → 50+ vulnerability checks → enrichment (RAG/compliance/triage) → reports. Python 3.8+, MIT, v1.4.0 (code name **Hanzou**). Sync `requests` + `ThreadPoolExecutor` (not async).

## Commands

```bash
# Setup
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pytest, ruff
cp config/config.example.yaml config/config.yaml
# optional: pip install playwright && playwright install chromium
# optional TLS evasion: pip install curl_cffi

# Run
python deep_eye.py -u https://example.com
python deep_eye.py -c config/config.yaml -v
python deep_eye.py -u https://example.com --formats junit,csv,xlsx
python deep_eye.py --diff baseline.json current.json --diff-format html
python deep_eye.py -u https://example.com --retest-new baseline.json
python deep_eye.py -u https://example.com --scope-nl "only /api/* no /logout host target.com"

# CVE / RAG
python scripts/update_cve_database.py
python scripts/build_cve_rag_index.py

# Tests
pytest
pytest tests/test_features_1_19.py tests/test_bugfix_gaps.py -v
pytest tests/test_template_engine.py tests/test_export_formats.py -v
python tests/e2e_litellm.py   # needs API key
```

Windows install: `.\scripts\install.ps1` (creates `.deep-venv/`).

## Architecture

**Scan flow:**
```
CLI → ScannerEngine.scan
  → login_replay? → recon? → subdomain?
  → crawl + OpenAPI seed?
  → AI planner? (threads/max_urls/order)
  → per-URL: challenge_solver? captcha skip? payloads → VulnerabilityScanner
       → browser? plugins? templates? extra modules? secrets?
  → dedupe fingerprints
  → FP replay? evidence summary?
  → RAG → compliance → AI triage → bounty
  → ReportGenerator + notifications
  → checkpoint save
```

### Layers

| Layer | Purpose |
|-------|---------|
| `core/` | Orchestration, built-in checks, payloads, reports, plugins, diff, state |
| `ai_providers/` | `generate(prompt, **kwargs) -> str` + `AIProviderManager` failover |
| `modules/` | Attack modules (ctor `(http_client, config)`, `scan(url, context) -> List[Dict]`) |
| `utils/` | HTTP, config, exports, compliance, scope, OAST, fingerprints, NL scope |
| `config/` | `config.example.yaml` is source of truth |
| `templates/` | Nuclei-style YAML (not report Jinja; reports use Jinja in report_generator) |
| `plugins/` | `PluginBase` drop-ins |
| `scripts/` | CVE DB + RAG builders |
| `.agents/skills/` | Agent skills: pentest, bug-bounty, red-team, blue-team, ctf, security-ops |

### Agent skills

When the user asks for pentest / bug bounty / red team / blue team / CTF work, load the matching skill from `.agents/skills/<name>/SKILL.md` (router: `security-ops`). Skills assume **authorized** targets only and point at this repo’s CLI/config/modules.

See `docs/SKILLS.md` and `.agents/skills/README.md`.

### Module categories

**Core / classic:** api_security, authentication, browser_automation, business_logic, cve_intelligence, file_upload, ml_detection, payload_obfuscation, reconnaissance, reporting, secrets_scanner, websocket, collaboration

**v1.4+ attack classes:** nosql_injection, http_smuggling, race_condition, log4shell, mass_assignment, prototype_pollution, oauth_testing, cache_poisoning, subdomain_takeover, directory_bruteforce, port_scanner, saml_attacks, secret_scanning

**Hanzou-era (config-gated):** ai_triage, captcha_detection, login_replay, template_engine, challenge_solver, intercepting_proxy

**Feature pack (enabled_checks):** cors_csp, jwt_deep, graphql_deep, idor, stored_xss, email_injection, cache_deception, h2_smuggle, supply_chain_js, waf_fingerprint, ssrf_cloud

**Pipeline helpers:** openapi_ingest, auth_session, ai_planner, evidence_summary, fp_replay

### Key design rules

- **Config-driven:** CLI is thin (`-u/-c/-v/--formats/--diff*/--retest-new/--scope-nl`). Behavior in YAML.
- **Threads:** 1–50; crawl pool `min(threads, 10)`.
- **Vuln dict:** `type`, `severity` (critical|high|medium|low|info), `url`, `parameter`, `payload`, `evidence`, `remediation`; optional `cve_references`, `fingerprint`, `plugin`, `ai_evidence_summary`.
- **PDF:** ReportLab only (not WeasyPrint on Windows).
- **OAST:** `scanner.oast_callback_url` or `oast.enabled` local server.
- **TLS evasion:** `tls_evasion.enabled` + `curl_cffi` if installed.
- **Dedupe:** `reporting.dedupe` (default true) via `utils/finding_fingerprint.py`.
- **Deferred:** full async/httpx rewrite (Group I); plugin OS sandbox.

## Development patterns

### Add a vulnerability check (module)

1. `modules/<name>/` with `__init__.py` + tester class
2. Ctor `(http_client, config)`; `scan(url, context=None) -> List[Dict]`
3. Register in `VulnerabilityScanner._feature_testers` **or** `ScannerEngine._init_extra_module_testers`
4. Add name to `config.example.yaml` → `vulnerability_scanner.enabled_checks`
5. Prefer new module over growing `vulnerability_scanner.py` further

### Add built-in `_check_*`

Only for small core checks: method on `VulnerabilityScanner`, gate on `enabled_checks`, wrap `state_manager.start_attack/end_attack`.

### Add AI provider

1. `ai_providers/<name>_provider.py` with `generate(prompt, **kwargs) -> str`
2. Register in `provider_manager._initialize_providers`
3. Config block under `ai_providers.<name>`

### Add export format

1. Pure builder in `utils/exports/`
2. Export from `utils/exports/__init__.py`
3. Wire in `report_generator` / CLI formats

## Important context

- Authorized targets only
- Venv: `.deep-venv/` (install scripts use this name)
- SQLite: `data/deep_eye.db`, `data/cve_intelligence.db`
- RAG: TF-IDF pickle index (`modules/cve_intelligence/rag_index.py`), not only ChromaDB docs elsewhere may be stale
- Hierarchical `AGENTS.md` under core/, modules/, utils/, tests/, packages
- `CONTRIBUTING.md`: use `modules/<name>/` (not obsolete `modules/exploits/`)
