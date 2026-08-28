# MODULES KNOWLEDGE BASE

**Scope:** `modules/` only. See `docs/MODULES.md` for full tables.

## OVERVIEW
Attack packages + pipeline helpers. Standard: `(http_client, config)` + `scan(url, context=None) -> List[Dict]`.

## WIRING
| Path | Examples |
|------|----------|
| Classic imports in VulnerabilityScanner | api_security, nosql, oauth, … |
| `_feature_testers` | cors_csp, jwt_deep, graphql_deep, idor, stored_xss, email_injection, cache_deception, h2_smuggle, supply_chain_js, waf_fingerprint, ssrf_cloud, host_header_deep, hpp_pollution, open_redirect_deep, crlf_header_inject_deep, ssti_engines, http_method_override, api_bola_deep, websocket_deep, sse_injection, cloud_misconfig, php_webshell, frida_mobile, android_static, ios_plist, mobile_ssl_pinning, mobile_ai_chain |
| Engine extras | directory_bruteforce, port_scanner, saml_attacks, subdomain_takeover, cache_poisoning |
| Engine lifecycle | openapi_ingest, auth_session, ai_planner, evidence_summary, fp_replay, template_engine, challenge_solver, login_replay, captcha, intercepting_proxy, ai_triage, cve_intelligence |

## CONVENTIONS
- Package + `__init__.py` export + register + `enabled_checks` / config block
- Child AGENTS: template_engine, cve_intelligence, ai_triage

## ANTI-PATTERNS
- Import ScannerEngine from testers (cycles)
- Merge secrets_scanner / secret_scanning casually
- Skip config gates for side-effectful services
