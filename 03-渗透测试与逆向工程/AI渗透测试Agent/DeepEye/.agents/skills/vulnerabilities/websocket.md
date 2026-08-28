# WebSocket Security

**Trigger condition:** WS upgrade endpoints; checks `websocket`, `websocket_deep`.

## Overview
WebSockets need origin/auth checks; CSWSH and message injection are common.

## Detection
```text
# websocket_deep
python deep_eye.py -u <target>
```

**Indicators:**
- 101 upgrade with evil Origin
- Handshake reflection findings

## Testing Checklist

### Test 1: Origin
**Tool:** `websocket_deep`
**What to look for:** CSWSH / Origin accepted

### Test 2: Handshake inject
**Tool:** `websocket_deep`
**What to look for:** Header reflection

## Key Payloads
```
Origin: https://evil.example
Sec-WebSocket-Protocol: <script>
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `websocket`, `websocket_deep` | Upgrade probes |

## Exploitation (When Vulnerability is Confirmed)
1. Show cross-origin subscribe/action
2. Impact: account actions as victim
3. Bind session to origin + auth

## Common Bypasses
- null Origin
- subdomain Origin tricks

## Remediation Summary
- Strict Origin allowlist
- Authenticate before upgrade
