# JWT Authentication Attacks

**Trigger condition:** `Bearer eyJ...` tokens; checks `jwt_deep`, `jwt_vulnerabilities`.

## Overview
Misconfigured JWTs: alg none, weak secrets, kid injection, alg confusion.

## Detection
```text
# jwt_deep in enabled_checks
python deep_eye.py -u <target>
```

**Indicators:**
- JWT in cookie/header/body
- Findings from `jwt_deep`

## Testing Checklist

### Test 1: alg none
**Tool:** `jwt_deep`
**What to look for:** Unsigned token accepted

### Test 2: Weak secret
**Tool:** config `jwt_deep.weak_secrets`
**What to look for:** Forged signature accepted

### Test 3: kid abuse
1. Path traversal / SQLi in kid
2. Observe error or bypass
3. Document

## Key Payloads
```
{"alg":"none"}
HS256 with secret "secret"
kid: ../../dev/null
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `jwt_deep` | Auto JWT tests |

## Exploitation (When Vulnerability is Confirmed)
1. Forge token for other user/admin
2. Hit protected endpoint
3. Report before/after (redact secrets)

## Common Bypasses
- RS256→HS256 confusion
- Claim `role`/`admin` edit

## Remediation Summary
- Allowlist algorithms; reject none
- Strong secrets / proper key management
