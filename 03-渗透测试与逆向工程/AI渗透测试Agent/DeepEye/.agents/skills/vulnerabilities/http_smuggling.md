# HTTP Request Smuggling

**Trigger condition:** Front-end/proxy chains; checks `http_smuggling`, `h2_smuggle`.

## Overview
CL.TE/TE.CL desync between proxies and backends enables request hijacking.

## Detection
```text
# http_smuggling, h2_smuggle
python deep_eye.py -u <target>
```

**Indicators:**
- Timing/desync findings
- Ambiguous CL/TE acceptance

## Testing Checklist

### Test 1: Classic smuggle
**Tool:** `http_smuggling`
**What to look for:** Desync evidence in finding

### Test 2: H2
**Tool:** `h2_smuggle`
**What to look for:** h2c / CL+TE ambiguity

## Key Payloads
```
Content-Length + Transfer-Encoding: chunked conflict
TE.CL / CL.TE probe bodies (module corpus)
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `http_smuggling`, `h2_smuggle` | Probes |

## Exploitation (When Vulnerability is Confirmed)
1. Document desync request pair
2. Impact: cache poison / credential capture (authorized only)
3. Fix proxy parsing consistency

## Common Bypasses
- Obfuscated TE headers
- HTTP/2 downgrade

## Remediation Summary
- Normalize CL/TE at edge
- Reject ambiguous requests
