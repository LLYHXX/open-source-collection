# Deep Eye CLI

**Trigger condition:** Any authorized scan with this repository.

## Overview
Primary entrypoint for automated web/API testing in this project.

## Detection
N/A

## Testing Checklist

### Test 1: Setup
**Tool:** `python deep_eye.py --setup`
**What to look for:** `config/config.yaml` created

### Test 2: Scan
**Tool:** `python deep_eye.py -u https://TARGET -v --formats html,json`
**What to look for:** Report under `reports/`

### Test 3: Scope / retest
**Tool:** `--scope-nl` / `--retest-new baseline.json`
**What to look for:** Filtered URLs / only new findings

## Key Payloads
N/A — configure via YAML `enabled_checks`

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Wizard | `python deep_eye.py --setup` | Config |
| Scan | `python deep_eye.py -u URL -v` | Full run |
| Scope | `--scope-nl "..."` | NL scope |
| Diff | `--diff a.json b.json` | Compare |
| Retest | `--retest-new base.json` | Delta |

## Exploitation
N/A

## Common Bypasses
N/A

## Remediation Summary
N/A
