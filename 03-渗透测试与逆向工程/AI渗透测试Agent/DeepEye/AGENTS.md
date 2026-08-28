# PROJECT KNOWLEDGE BASE

**Generated:** 2026-07-15  
**Branch:** dev/hanzou  
**Version:** 1.4.0 Hanzou

## OVERVIEW

AI-driven pentest tool (Python 3.8+). Multi-provider AI payloads → crawl/OpenAPI seed → 50+ checks → dedupe → RAG/compliance/triage → reports. Sync `requests` + `ThreadPoolExecutor`.

## STRUCTURE

```
deep-eye/
├── deep_eye.py          # CLI: -u/-c/-v/--formats/--diff*/--retest-new/--scope-nl
├── core/                # ScannerEngine, VulnerabilityScanner, payloads, reports, plugins
├── ai_providers/        # generate() + AIProviderManager
├── modules/             # Attack + pipeline modules (see docs/MODULES.md)
├── utils/               # HTTP, scope, OAST, exports, fingerprint, nl_scope
├── config/              # config.example.yaml = source of truth
├── templates/           # Nuclei-style YAML (exposures/, misconfig/)
├── plugins/             # PluginBase drop-ins
├── .agents/skills/      # Skills: workflows + vulnerabilities/payloads/tools (loader: proxy/system.py)
├── proxy/               # system.py skill discovery → <available_skills>
├── scripts/             # CVE DB + RAG index
├── tests/               # pytest (+ e2e_litellm.py script)
├── docs/                # User docs (CONFIGURATION, MODULES, ARCHITECTURE, …)
├── data/                # SQLite + auth_sessions + RAG pickle
└── reports/             # Scan output (gitignored)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| CLI / retest / NL scope | `deep_eye.py` | `--retest-new`, `--scope-nl` |
| Scan lifecycle | `core/scanner_engine.py` | Crawl, OpenAPI, planner, post-process |
| Per-URL checks | `core/vulnerability_scanner.py` | `_check_*` + `_feature_testers` |
| Feature modules | `modules/<name>/` | cors_csp, jwt_deep, idor, … |
| Dedupe fingerprints | `utils/finding_fingerprint.py` | `reporting.dedupe` |
| NL scope | `utils/nl_scope.py` | → `scope` config |
| OpenAPI seed | `modules/openapi_ingest/` | `openapi.enabled` |
| Auth roles | `modules/auth_session/` | multi-cookie roles |
| AI planner / evidence / FP replay | `modules/ai_planner/`, `evidence_summary/`, `fp_replay/` | post-scan pipeline |
| Templates | `modules/template_engine/` + `templates/` | config `templates` |
| Challenge / login / captcha / proxy | respective `modules/*` | config-gated in engine |
| Exports | `utils/exports/` | junit/csv/xlsx/diff |
| Agent skills | `.agents/skills/` | workflows + vulnerabilities/payloads/tools; loader `proxy/system.py` |
| Full knobs | `config/config.example.yaml` | |

## CODE MAP

| Symbol | Location | Role |
|--------|----------|------|
| `main` | `deep_eye.py` | CLI, onboard, retest filter |
| `ScannerEngine` | `core/scanner_engine.py` | Lifecycle owner |
| `VulnerabilityScanner` | `core/vulnerability_scanner.py` | Per-URL checks |
| `AIPayloadGenerator` | `core/ai_payload_generator.py` | AI/static payloads + OAST URL |
| `ReportGenerator` | `core/report_generator.py` | HTML/PDF/JSON + formats |
| `AIProviderManager` | `ai_providers/provider_manager.py` | Failover `generate()` |
| `dedupe_findings` | `utils/finding_fingerprint.py` | Collapse dupes |
| `parse_nl_scope` | `utils/nl_scope.py` | NL → scope dict |
| `ScopeManager` | `utils/scope_manager.py` | Host/path/port allow |

**Flow:** CLI → engine → (login) → recon? → crawl + OpenAPI? → planner? → scan_url (checks) → dedupe → FP replay → evidence summary → RAG → compliance → triage → bounty → report → checkpoint.

## CONVENTIONS

- Config-driven; extend YAML not CLI for scan knobs (CLI only thin flags above).
- Vuln dict: `type`, `severity`, `url`, `parameter`, `payload`, `evidence`, `remediation` (+ optional fingerprint).
- Module: `(http_client, config)`, `scan(url, context=None) -> List[Dict]`.
- Feature checks: add to `_feature_testers` list in `vulnerability_scanner.py` + `enabled_checks`.
- Extra engine modules (dirb/port/…): `_init_extra_module_testers`.
- Paths: `pathlib.Path`. PDF: ReportLab. Venv: `.deep-venv/`.

## ANTI-PATTERNS

- Unauthorized targets.
- Full async rewrite without dedicated Group I branch.
- WeasyPrint as default PDF.
- Inventing result keys that break report/export/diff.
- Skipping `enabled_checks` / config gates.
- Committing secrets in `config.yaml`.
- Growing `vulnerability_scanner.py` instead of new `modules/`.

## COMMANDS

```bash
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml
python deep_eye.py -u https://example.com --scope-nl "only /api/*" --retest-new baseline.json
pytest tests/test_features_1_19.py -v
```

## NOTES

- Child AGENTS.md under `core/`, `modules/`, `utils/`, `tests/`, and select packages.
- User docs: `docs/CONFIGURATION.md`, `MODULES.md`, `ARCHITECTURE.md`, `QUICKSTART.md`, `SCAN_FLOW.md`.
- See `CLAUDE.md` for agent-oriented development patterns.
