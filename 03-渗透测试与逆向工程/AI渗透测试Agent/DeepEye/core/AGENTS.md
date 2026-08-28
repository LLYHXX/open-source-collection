# CORE KNOWLEDGE BASE

## OVERVIEW
Scan lifecycle owner: crawl, OpenAPI seed, per-URL checks, post-process (dedupe/RAG/triage), report.

## STRUCTURE
| File | Purpose |
|------|---------|
| `scanner_engine.py` | Lifecycle, ThreadPool, OpenAPI, planner, templates, extras, post-process |
| `vulnerability_scanner.py` | `_check_*` + `_feature_testers` dispatch |
| `ai_payload_generator.py` | AI/static payloads + OAST URL from config |
| `report_generator.py` | HTML/PDF/JSON/SARIF + exports |
| `pentest_state_manager.py` | Phases, progress, checkpoint |
| `plugin_manager.py` | Multi-class PluginBase load |
| `scan_diff.py` | Diff / retest identity helpers |
| `subdomain_scanner.py` | Experimental subdomain scan |

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Wire pipeline step | `scanner_engine.scan` |
| Add feature check | `_feature_testers` in `vulnerability_scanner.py` |
| Add heavy module | `_init_extra_module_testers` in `scanner_engine.py` |
| Diff identity | `scan_diff._identity_no_sev` |

## CONVENTIONS
- Ctor: `VulnerabilityScanner(config, http_client)` (reversed vs modules)
- Post-scan order: dedupe → FP replay → evidence → RAG → compliance → triage → bounty
- Prefer new `modules/` over growing `vulnerability_scanner.py`

## ANTI-PATTERNS
- Skip `enabled_checks` gates
- Invent vuln keys that break export/diff
- Put scan knobs on CLI (use YAML)
