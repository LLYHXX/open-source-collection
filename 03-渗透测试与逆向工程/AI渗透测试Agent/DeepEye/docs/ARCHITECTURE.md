# Architecture

## Overview

Deep Eye is a **config-driven**, multi-threaded penetration testing tool. `ScannerEngine` owns the lifecycle; `VulnerabilityScanner` owns per-URL checks; modules are pluggable packages under `modules/`.

Stack: **Python 3.8+**, sync **`requests`** (optional **`curl_cffi`** for TLS evasion), **`ThreadPoolExecutor`**, ReportLab PDF, YAML config.

## Pipeline

```
CLI (deep_eye.py)
  │  --scope-nl, --retest-new, --formats, --diff
  ▼
ScannerEngine.scan()
  ├─ Login replay (optional)
  ├─ Recon / subdomain (optional)
  ├─ Crawl + OpenAPI seed (optional)
  ├─ AI planner (optional) → threads / max_urls
  ├─ Per-URL parallel scan
  │    payloads → VulnerabilityScanner → browser/plugins/templates/extras/secrets
  ├─ Dedupe → FP replay → evidence summary
  ├─ RAG → compliance → AI triage → bounty
  └─ ReportGenerator + notifications + checkpoint
```

Detail: [SCAN_FLOW.md](SCAN_FLOW.md).

## Layers

### `core/`

| File | Role |
|------|------|
| `scanner_engine.py` | Lifecycle, crawl, OpenAPI, planner hooks, post-process |
| `vulnerability_scanner.py` | Built-in `_check_*` + `_feature_testers` dispatch |
| `ai_payload_generator.py` | AI/static payloads; OAST callback URL |
| `report_generator.py` | HTML/PDF/JSON/SARIF + export builders |
| `pentest_state_manager.py` | Phases, attack progress, checkpoint |
| `scan_diff.py` | Baseline vs current finding identity |
| `plugin_manager.py` | Load all `PluginBase` subclasses per file |
| `subdomain_scanner.py` | Experimental subdomain scan |

### `ai_providers/`

Contract: `generate(prompt, **kwargs) -> str`.  
`AIProviderManager`: enable-gated init, retry, failover, reject empty responses.

### `modules/`

Standard tester:

```python
class XTester:
    def __init__(self, http_client, config: dict): ...
    def scan(self, url: str, context=None) -> list[dict]: ...
```

Registration:

- **Feature checks** → `VulnerabilityScanner._feature_testers` + `enabled_checks`
- **Heavy extras** (dirb, port, …) → `ScannerEngine._init_extra_module_testers`
- **Pipeline services** (OpenAPI, planner, triage, …) → called from `ScannerEngine.scan`

Catalog: [MODULES.md](MODULES.md).

### `utils/`

| Area | Files |
|------|--------|
| HTTP | `http_client.py` (TokenBucket, optional curl_cffi) |
| Config | `config_loader.py`, `onboard.py` |
| Scope | `scope_manager.py`, `nl_scope.py` |
| OAST | `oast_server.py` |
| Findings | `finding_fingerprint.py` |
| Exports | `exports/*` |
| Compliance | `compliance/*` |

## Data contracts

### Vulnerability dict

Required for reporting/diff:

- `type`, `severity`, `url`, `evidence`, `remediation`  
Optional: `parameter`, `payload`, `fingerprint`, `cve_references`, `plugin`, `ai_evidence_summary`, `false_positive`, `compliance`

### Identity (diff / retest-new)

`(type, normalized_url, parameter)` — see `core/scan_diff._identity_no_sev`.

### Fingerprint (dedupe)

SHA-256 prefix of `type|path|parameter|root_cause_hint` — `utils/finding_fingerprint.py`.

## Threading model

| Pool | Workers |
|------|---------|
| Crawl | `min(threads, 10)` |
| Scan | `threads` (1–50) |
| Subdomain | capped low |

Shared `HTTPClient`; aggregate findings under a lock.

## Extension points

| Goal | Where |
|------|--------|
| New check | `modules/<name>/` + `_feature_testers` + `enabled_checks` |
| New CLI flag | `deep_eye.py` only if truly global; else YAML |
| New export | `utils/exports/` + `__init__.py` |
| New AI vendor | `ai_providers/` + `provider_manager` |
| New plugin | `plugins/*.py` extending `PluginBase` |

## Explicit non-goals (deferred)

- Full async/`httpx` rewrite (design: Group I, single dedicated branch)
- WeasyPrint as default PDF
- In-process custom DNS (OS-level only)
- Plugin process sandbox

## Related

- [CONFIGURATION.md](CONFIGURATION.md)  
- [MODULES.md](MODULES.md)  
- [QUICKSTART.md](QUICKSTART.md)  
- Root `AGENTS.md` / `CLAUDE.md` for agent orientation  
