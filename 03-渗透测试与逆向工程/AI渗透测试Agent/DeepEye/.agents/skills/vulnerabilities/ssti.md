# Server-Side Template Injection (SSTI)

**Trigger condition:** Template math evaluates; checks `ssti`, `ssti_engines`.

## Overview
Template engines evaluate attacker expressions; can become RCE.

## Detection
```text
python deep_eye.py -u <target>
# ssti, ssti_engines
```

**Indicators:**
- `{{7*7}}` → `49`
- Engine-specific errors

## Testing Checklist

### Test 1: Polyglot
**Tool:** `ssti`
**What to look for:** Evaluated math in body

### Test 2: Engine ID
**Tool:** `ssti_engines`
**What to look for:** Engine-named finding

## Key Payloads
```
{{7*7}}
${7*7}
<%= 7*7 %>
#{7*7}
{{config}}
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `ssti`, `ssti_engines` | Detect |

## Exploitation (When Vulnerability is Confirmed)
1. Confirm evaluation
2. RCE only on authorized labs
3. Report engine + minimal PoC

## Common Bypasses
- Alternate delimiters
- Sandbox escapes (lab only)

## Remediation Summary
- Never render user input as templates
- Logic-less / sandboxed engines
