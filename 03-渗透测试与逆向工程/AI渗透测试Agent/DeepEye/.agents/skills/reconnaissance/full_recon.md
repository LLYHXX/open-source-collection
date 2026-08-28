# Full Recon SOP (Deep Eye)

**Trigger condition:** New target engagement; `scanner.enable_recon: true`; user asks for recon.

## Overview
Structured recon before deep exploitation. Prefer passive then active within scope.

## Detection
```text
python deep_eye.py -u <target> -v
# scanner.enable_recon: true
```

## Testing Checklist

### Phase 1: Scope
1. Confirm RoE hosts/paths
2. Apply `--scope-nl` or `scope` YAML
3. Success: out-of-scope paths excluded

### Phase 2: Passive stack
1. Headers Server/X-Powered-By
2. OpenAPI/Swagger discovery
3. Success: stack notes for payload gen

### Phase 3: Crawl + OpenAPI
```text
openapi.enabled: true
openapi.source: <url-or-file>
python deep_eye.py -u <target>
```
**What to look for:** Seeded API endpoints in scan queue

### Phase 4: Auth surface
1. Login forms / OAuth / JWT cookies
2. Enable `login_replay` / `auth_session` if credentials allowed
3. Success: authenticated crawl

## Key Payloads
N/A — recon phase

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye recon | `enable_recon` | DNS/tech/OSINT modules |
| OpenAPI | `openapi` config | Endpoint seed |
| NL scope | `--scope-nl` | Scope lock |

## Exploitation
N/A — transition to vuln skills when surface mapped.

## Common Bypasses
N/A

## Remediation Summary
N/A for recon; document assets for defenders.
