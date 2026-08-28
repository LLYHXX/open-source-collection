# Next.js Notes

**Trigger condition:** `_next/`, Next.js headers, React/Next stack fingerprint.

## Overview
Focus middleware auth gaps, server actions, open redirects, cache.

## Detection
```text
python deep_eye.py -u <target>
# look for /_next/static, x-powered-by next
```

## Testing Checklist

### Test 1: Middleware bypass paths
**Tool:** Manual + Deep Eye crawl
**What to look for:** Protected route accessible via alt path

### Test 2: Redirect
**Tool:** `open_redirect_deep`
**What to look for:** Open redirect on next/callback

## Key Payloads
```
/_next/ data routes enumeration
?redirect=//evil.example
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | crawl + open_redirect_deep | Surface |

## Remediation Summary
- Enforce auth in middleware + handlers
- Validate redirects
