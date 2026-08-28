# SSRF

**Trigger condition:** URL/fetch/webhook params; checks `ssrf`, `ssrf_cloud`, `cloud_misconfig`.

## Overview
Server fetches attacker-chosen URLs — often internal services or cloud metadata.

## Detection
```text
# enable ssrf + ssrf_cloud
python deep_eye.py -u <target>
```

**Indicators:**
- Finding `SSRF` / cloud metadata
- Body contains `ami-id`, `instance-id`, `meta-data`

## Testing Checklist

### Test 1: Core SSRF
**Tool:** Deep Eye `ssrf`
**What to look for:** localhost/internal markers

### Test 2: Cloud metadata
**Tool:** `ssrf_cloud`
**What to look for:** AWS/GCP/Azure indicators

### Test 3: Blind OAST
1. Set `scanner.oast_callback_url`
2. Inject collaborator URL
3. Confirm DNS/HTTP hit

## Key Payloads
```
http://127.0.0.1
http://169.254.169.254/latest/meta-data/
http://metadata.google.internal/computeMetadata/v1/
http://[::1]/
file:///etc/passwd
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `ssrf`, `ssrf_cloud` | Probes |
| OAST | `oast_callback_url` | Blind SSRF |

## Exploitation (When Vulnerability is Confirmed)
1. Document internal/metadata hit
2. Impact: credentials / internal scan
3. Stay in scope

## Common Bypasses
- Decimal/hex/IPv6 IP encodings
- DNS rebinding / `localtest.me`
- Open redirect to metadata

## Remediation Summary
- Host/scheme allowlists; block link-local
- IMDSv2 / require metadata headers
