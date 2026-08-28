# Business Logic Flaws

**Trigger condition:** Checkout/price/qty/workflow multi-step; check `business_logic`, `race_condition`.

## Overview
Logic bugs abuse intended workflows without classic injection — price, step skip, race.

## Detection
```text
# business_logic, race_condition, mass_assignment
python deep_eye.py -u <target>
```

**Indicators:**
- Negative price / qty accepted
- Parallel requests double-spend

## Testing Checklist

### Test 1: Parameter tamper
**Tool:** `business_logic`, `mass_assignment`
**What to look for:** Privileged fields accepted

### Test 2: Race
**Tool:** `race_condition`
**What to look for:** Duplicate success

### Test 3: Workflow skip
1. Map multi-step flow
2. Jump to final step
3. Observe success without prior steps

## Key Payloads
```
price=-1
quantity=999999
role=admin (mass assign)
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | business_logic, race_condition, mass_assignment | Heuristics |

## Exploitation (When Vulnerability is Confirmed)
1. Show financial/state impact
2. Minimal request sequence
3. Server-side state machine fixes

## Common Bypasses
- Hidden fields in client
- Replay old steps

## Remediation Summary
- Server-side price/qty validation
- Atomic operations; step tokens
