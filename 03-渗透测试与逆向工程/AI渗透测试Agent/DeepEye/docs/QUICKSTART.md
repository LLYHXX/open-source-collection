# Quick Start Guide

## Installation

```bash
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml
# Edit config.yaml — set at least one AI provider API key
```

**Windows:**
```powershell
.\scripts\install.ps1
# activates .deep-venv
```

**Linux/macOS:**
```bash
chmod +x scripts/install.sh && ./scripts/install.sh
source .deep-venv/bin/activate
```

Optional:
```bash
pip install playwright && playwright install chromium
pip install curl_cffi          # tls_evasion
pip install -r requirements-dev.txt   # pytest, ruff
```

## First run

```bash
python deep_eye.py -u https://target.com
```

If `config/config.yaml` is missing, the onboard wizard runs and writes it.

## Common commands

```bash
# Scan
python deep_eye.py -u https://target.com
python deep_eye.py -c config/config.yaml -v
python deep_eye.py -u https://target.com --formats junit,csv,xlsx

# Natural-language scope
python deep_eye.py -u https://target.com --scope-nl "only /api/* no /logout host target.com"

# Diff two result JSONs
python deep_eye.py --diff baseline.json current.json --diff-format html

# Keep only findings NEW vs a baseline (after a full scan)
python deep_eye.py -u https://target.com --retest-new reports/baseline.json

# CVE intelligence
python scripts/update_cve_database.py
python scripts/build_cve_rag_index.py

# Tests
pytest
pytest tests/test_features_1_19.py -v
```

## CLI reference

| Flag | Description |
|------|-------------|
| `-u, --url` | Target URL (overrides config) |
| `-c, --config` | Config path (default `config/config.yaml`) |
| `-v, --verbose` | Verbose logging |
| `--no-banner` | Hide banner |
| `--version` | Version string |
| `--formats` | Comma-separated: `html,pdf,json,junit,csv,xlsx,sarif` |
| `--diff BASELINE CURRENT` | Diff mode (no scan) |
| `--diff-output` | Diff report path |
| `--diff-format` | `html` \| `json` \| `csv` |
| `--retest-new BASELINE` | After scan, drop findings already in baseline |
| `--scope-nl TEXT` | NL scope → `scope` config (hosts, paths, ports) |

## Minimal config

```yaml
ai_providers:
  openai:
    enabled: true
    api_key: "sk-..."
    model: "gpt-4o"

scanner:
  target_url: "https://target.com"
  default_threads: 5
  default_depth: 2
  ai_provider: "openai"

vulnerability_scanner:
  enabled_checks:
    - sql_injection
    - xss
    - ssrf
    - cors_csp
    - jwt_deep

reporting:
  enabled: true
  formats: [html, json]
  dedupe: true
```

## Useful optional blocks

```yaml
# OpenAPI seed
openapi:
  enabled: true
  source: "https://target.com/openapi.json"

# Challenge / login / templates
challenge_solver: { enabled: true }
login_replay:
  enabled: true
  macro_path: "config/login_macro.json"
templates:
  enabled: true
  template_directories: ["templates"]

# AI post-processing
ai_triage: { enabled: true }
ai_planner: { enabled: true }
evidence_summary: { enabled: true, min_severity: high }
fp_replay: { enabled: true }

# Scope
scope:
  enabled: true
  allowed_hosts: ["*.target.com"]
  path_allow: ["/api/*"]
```

## Reports

Default directory: `reports/`. Formats from `reporting.formats` or `--formats`.

## Legal

**Authorized testing only.** You must own the target or have written permission.

## Next reading

- [CONFIGURATION.md](CONFIGURATION.md) — full YAML reference  
- [MODULES.md](MODULES.md) — module catalog  
- [SCAN_FLOW.md](SCAN_FLOW.md) — phase pipeline  
- [ARCHITECTURE.md](ARCHITECTURE.md) — layers and data shapes  
