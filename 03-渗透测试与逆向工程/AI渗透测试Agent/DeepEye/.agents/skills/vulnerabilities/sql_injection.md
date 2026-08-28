# SQL Injection

**Trigger condition:** Params reflect DB errors, login forms, `?id=` endpoints, or `sql_injection` in enabled_checks.

## Overview
Attacker alters SQL via user input. Critical when auth bypass or data extract is possible.

## Detection
```text
python deep_eye.py -u <target> -v
# ensure sql_injection in vulnerability_scanner.enabled_checks
```

**Indicators in tool output:**
- MySQL/Postgres/MSSQL/SQLite error strings
- Finding type containing `SQL Injection`

## Testing Checklist

### Test 1: Automated probe
**Tool:** `python deep_eye.py -u <url> -c config/config.yaml`
**What to look for:** Finding with SQL error/`evidence` differential

### Test 2: Multi-surface
**Tool:** Deep Eye multi-surface inject (`core/injection_surfaces.py`)
**What to look for:** Body/JSON injection, not only query

### Test 3: Manual confirm
1. Replay payload with curl/Burp
2. Confirm error or boolean/time differential
3. Save minimal request/response

## Key Payloads
```
' OR '1'='1
' OR '1'='1' --
' UNION SELECT NULL--
' AND 1=2--
' AND SLEEP(3)--
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `python deep_eye.py -u URL` | Auto SQLi |
| sqlmap | `sqlmap -u URL --batch` | Confirm (authorized only) |

## Exploitation (When Vulnerability is Confirmed)
1. Document exact request/response
2. Prove impact (auth bypass / data read) on authorized target only
3. Report type, severity, payload, remediation (parameterized queries)

## Common Bypasses
- **WAF:** `/**/` comments, case mix `UnIoN`
- **Encoding:** double URL encode
- **Edge:** JSON body / second-order

## Remediation Summary
- Parameterized queries / bound parameters
- Least-privilege DB accounts
