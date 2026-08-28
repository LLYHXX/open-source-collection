# Browser Automation (Deep Eye)

**Trigger condition:** JS-heavy apps, DOM XSS, login needs browser; config `advanced.enable_javascript_rendering`.

## Overview
Playwright-based tests for DOM XSS and form flows when enabled.

## Detection
```text
# config advanced.enable_javascript_rendering: true
# optional: playwright install chromium
python deep_eye.py -u <target>
```

## Testing Checklist

### Test 1: Enable browser
**Tool:** config flag + scan
**What to look for:** Browser module logs / DOM findings

### Test 2: Login macro
**Tool:** `login_replay` with Playwright step if present
**What to look for:** Authenticated session

## Key Payloads
DOM sinks vary — use `xss` skill payloads in browser context.

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Playwright | `pip install playwright && playwright install chromium` | Browser |
| Deep Eye | `advanced.enable_javascript_rendering` | Integration |

## Exploitation
Document browser-only sinks with screenshot if authorized.

## Common Bypasses
Client-only filters

## Remediation Summary
Same as XSS — encode + CSP
