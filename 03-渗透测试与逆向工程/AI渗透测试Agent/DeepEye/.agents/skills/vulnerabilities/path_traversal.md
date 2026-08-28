# Path Traversal / LFI / RFI

**Trigger condition:** file/path/page params; checks `path_traversal`, `lfi`, `rfi`, `php_webshell`.

## Overview
User-controlled paths read arbitrary files (LFI) or remote includes (RFI).

## Detection
```text
python deep_eye.py -u <target>
# path_traversal, lfi, rfi, php_webshell
```

**Indicators:**
- `root:x:0:0` or win.ini
- PHP filter base64 source

## Testing Checklist

### Test 1: Traversal
**Tool:** `lfi` / `path_traversal`
**What to look for:** passwd/win.ini markers

### Test 2: PHP wrappers
**Tool:** `php_webshell`
**What to look for:** `php://filter` leak

### Test 3: RFI + OAST
**Tool:** `rfi` + `oast_callback_url`
**What to look for:** include error or OAST hit

## Key Payloads
```
../../../etc/passwd
....//....//....//etc/passwd
php://filter/convert.base64-encode/resource=index.php
..%2f..%2f..%2fetc%2fpasswd
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | lfi/rfi/path_traversal/php_webshell | Auto |

## Exploitation (When Vulnerability is Confirmed)
1. Prove sensitive file read
2. No mass PII dump in reports
3. Allowlist file access

## Common Bypasses
- Double encoding
- Wrapper chains

## Remediation Summary
- Canonicalize + allowlist paths
- Disable dangerous PHP wrappers
