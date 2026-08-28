# UTILS

Shared infrastructure — no attack logic.

## STRUCTURE
| File / dir | Purpose |
|------------|---------|
| `http_client.py` | HTTPClient + TokenBucket; optional curl_cffi TLS evasion |
| `config_loader.py` / `onboard.py` | YAML load + wizard |
| `scope_manager.py` / `nl_scope.py` | Scope allow/deny + NL parse |
| `finding_fingerprint.py` | Fingerprint + dedupe |
| `oast_server.py` | Local OAST listener |
| `exports/` | junit/csv/xlsx/diff builders |
| `compliance/` | Framework JSON mapping |
| `logger.py`, `parser.py`, `notification_manager.py` | Cross-cutting |

## CONVENTIONS
- One shared HTTPClient from engine
- Export builders: pure functions, register in `exports/__init__.py`
- Scope supports optional `path_allow`

## ANTI-PATTERNS
- Second HTTPClient per module
- Scan/payload logic inside utils
