# Cross-Site Scripting (XSS)

**Trigger condition:** Reflected params, HTML sinks, `xss`/`stored_xss` findings, weak CSP.

## Overview
Attacker script runs in victim browser. Impact depends on cookie flags and CSP.

## Detection
```text
python deep_eye.py -u <target>
# checks: xss, stored_xss, cors_csp
```

**Indicators:**
- Unencoded payload in body
- Finding type contains `XSS`
- CSP missing/`unsafe-inline`

## Testing Checklist

### Test 1: Reflected
**Tool:** Deep Eye `xss`
**What to look for:** Payload reflected without encoding

### Test 2: Stored
**Tool:** enable `stored_xss`
**What to look for:** Marker on sink URL after inject

### Test 3: Context
1. Identify HTML vs attr vs JS context
2. Adjust quotes/handlers
3. Review CSP via `cors_csp`

## Key Payloads
```
<script>alert(1)</script>
"><img src=x onerror=alert(1)>
<svg/onload=alert(1)>
javascript:alert(1)
'"><svg/onload=alert(document.domain)>
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `xss`, `stored_xss` | Auto reflect/store |
| Browser module | Playwright if enabled | DOM XSS |

## Exploitation (When Vulnerability is Confirmed)
1. Capture unescaped reflection
2. Impact only if session cookies accessible / CSP weak
3. Report context (reflected/stored/DOM)

## Common Bypasses
- Event handlers without `<script>`
- Nested SVG/math
- CSP: JSONP, nonce reuse

## Remediation Summary
- Context-aware encoding
- Strict CSP with nonces; no `unsafe-inline`
