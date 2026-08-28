# IDOR / BOLA

**Trigger condition:** Object IDs in path/query; checks `idor`, `api_bola_deep`.

## Overview
Change object IDs to access another user's resources (broken object-level authz).

## Detection
```text
python deep_eye.py -u https://api.target/users/1
# idor, api_bola_deep
```

**Indicators:**
- 200 + body length delta after ID swap
- Finding `Potential IDOR` / BOLA

## Testing Checklist

### Test 1: Sequential IDs
**Tool:** `idor`
**What to look for:** Different content for id±1

### Test 2: UUID / role headers
**Tool:** `idor` + `alt_headers`
**What to look for:** Foreign object data

### Test 3: Two-account manual
1. Create users A and B
2. As A, request B's object
3. Confirm data leak

## Key Payloads
```
/users/1 → /users/2
?account_id=100 → 101
base64 id increment
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `idor`, `api_bola_deep` | ID mutation |

## Exploitation (When Vulnerability is Confirmed)
1. Prove horizontal access A→B
2. Capture both responses (redact PII in reports)
3. Remediate with ownership checks

## Common Bypasses
- Encoded IDs
- Nested JSON user ids
- GraphQL object IDs

## Remediation Summary
- Authorize every object access server-side
- Opaque IDs do not replace authz
