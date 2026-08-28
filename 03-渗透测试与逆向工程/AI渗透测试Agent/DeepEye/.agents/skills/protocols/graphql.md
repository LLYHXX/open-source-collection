# GraphQL Testing

**Trigger condition:** `/graphql`, GraphiQL, `__schema` in body; check `graphql_deep`.

## Overview
GraphQL exposes rich query surface: introspection, batching, IDOR via objects, DoS via depth/aliases.

## Detection
```text
# graphql_deep
python deep_eye.py -u https://target/graphql
```

**Indicators:**
- Introspection data returned
- Batch/alias findings

## Testing Checklist

### Test 1: Introspection
**Tool:** `graphql_deep`
**What to look for:** `__schema` types listed

### Test 2: Batching / aliases
**Tool:** `graphql_deep`
**What to look for:** Large batch accepted

### Test 3: Authz on objects
1. Query other users' objects by ID
2. Compare with authorized session
3. Document BOLA

## Key Payloads
```
{ __schema { types { name } } }
batch of 50 {__typename}
query with 40 aliases
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `graphql_deep` | Introspection/DoS/vars |

## Exploitation (When Vulnerability is Confirmed)
1. Map sensitive fields via introspection
2. Prove unauthorized data read
3. Disable introspection in prod; authz per field

## Common Bypasses
- GET vs POST query
- Persisted query abuse

## Remediation Summary
- Disable introspection in production
- Depth/complexity limits; field authz
