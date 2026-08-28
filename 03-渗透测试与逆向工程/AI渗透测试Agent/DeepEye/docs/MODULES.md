# Modules Reference

Deep Eye modules are packages under `modules/`. Most attack modules share one interface; pipeline helpers differ slightly.

## Standard interface

```python
class ModuleName:
    def __init__(self, http_client, config: dict):
        ...

    def scan(self, url: str, context: dict | None = None) -> list[dict]:
        # vulnerability result dicts
        ...
```

**Result dict:** `type`, `severity`, `url`, `parameter`, `payload`, `evidence`, `remediation` (+ optional fields).

**Enable attack modules** via `vulnerability_scanner.enabled_checks` in config (not every package is on by default).

---

## Web application

| Package | Check key | Description |
|---------|-----------|-------------|
| `api_security` | `api_security`, `graphql_vulnerabilities` | OWASP API Top 10 + GraphQL basics |
| `graphql_deep` | `graphql_deep` | Batching, aliases, depth budget probes |
| `authentication` | `authentication` | Session / auth testing |
| `business_logic` | `business_logic` | Workflow / logic abuse |
| `file_upload` | `file_upload` | Upload bypasses |
| `websocket` | `websocket` | WS upgrade probes |
| `cors_csp` | `cors_csp` | CORS reflection, CSP gaps, Trusted Types |
| `idor` | `idor` | IDOR/BOLA ID/UUID/b64 swap + role-header delta |
| `stored_xss` | `stored_xss` | Second-order XSS inject + re-fetch |
| `email_injection` | `email_injection` | Header/CRLF on mail-like forms |
| `cache_deception` | `cache_deception` | Path normalization cache tricks |
| `supply_chain_js` | `supply_chain_js` | Third-party JS, SRI, outdated libs |
| `api_bola_deep` | `api_bola_deep` | API BOLA/IDOR + mass-assignment probes |
| `websocket_deep` | `websocket_deep` | CSWSH / origin / handshake injection |
| `sse_injection` | `sse_injection` | SSE endpoint discovery + event reflection |
| `cloud_misconfig` | `cloud_misconfig` | Bucket listing + metadata SSRF hints |
| `php_webshell` | `php_webshell` | PHP LFI wrappers + webshell path probes |

## Injection & protocol

| Package | Check key | Description |
|---------|-----------|-------------|
| `nosql_injection` | `nosql_injection` | NoSQL injection |
| `http_smuggling` | `http_smuggling` | Classic smuggling |
| `h2_smuggle` | `h2_smuggle` | h2c upgrade + CL/TE ambiguity |
| `host_header_deep` | `host_header_deep` | Host/XFH poisoning, reset-path severity boost |
| `hpp_pollution` | `hpp_pollution` | HTTP parameter pollution differential |
| `open_redirect_deep` | `open_redirect_deep` | Advanced open redirect / scheme confusion |
| `crlf_header_inject_deep` | `crlf_header_inject_deep` | CRLF response splitting / Set-Cookie |
| `ssti_engines` | `ssti_engines` | Multi-engine SSTI (Jinja/Twig/SpEL/FreeMarker…) |
| `http_method_override` | `http_method_override` | Verb tampering via override headers |
| `log4shell` | `log4shell` | JNDI / Log4j |
| `prototype_pollution` | `prototype_pollution` | JS prototype pollution |
| `mass_assignment` | `mass_assignment` | Mass assignment |
| `ssrf_cloud` | `ssrf_cloud` | Cloud metadata + bypass corpus (plus core SSRF) |
| `jwt_deep` | `jwt_deep` | alg=none, kid tricks |
| `oauth_testing` | `oauth_testing` | OAuth issues |
| `saml_attacks` | `saml_attacks` | SAML attacks |
| `race_condition` | `race_condition` | Concurrent races |

## Discovery & infra

| Package | Check / config | Description |
|---------|----------------|-------------|
| `reconnaissance` | `scanner.enable_recon` | DNS, WHOIS, OSINT, tech |
| `directory_bruteforce` | `directory_bruteforce` | Path brute |
| `port_scanner` | `port_scanner` | TCP ports |
| `subdomain_takeover` | `subdomain_takeover` | Dangling DNS |
| `cache_poisoning` | `cache_poisoning` | Cache poison headers |
| `waf_fingerprint` | `waf_fingerprint` | WAF ID + payload profile |
| `openapi_ingest` | `openapi.*` | OpenAPI/Swagger → URL seed |
| `secrets_scanner` | secrets + `secret_scanning` | Leaked secrets in responses |
| `secret_scanning` | (content scanner) | Pattern pack used with secret_scanning check |

## Mobile / Frida

| Package | Check key | Description |
|---------|-----------|-------------|
| `frida_mobile` | `frida_mobile` | Offline Frida hook scripts + AI payload advice |
| `android_static` | `android_static` | APK zip heuristics (debuggable, secrets) |
| `ios_plist` | `ios_plist` | Info.plist ATS + URL schemes |
| `mobile_ssl_pinning` | `mobile_ssl_pinning` | Pinning indicators in artifacts |
| `mobile_ai_chain` | `mobile_ai_chain` | Ordered mobile attack chain + payloads |

Enable with `mobile.enabled` + checks above in `enabled_checks`.

## Auth & automation

| Package | Config key | Description |
|---------|------------|-------------|
| `auth_session` | `auth_session` | Multi-role cookie/header store |
| `login_replay` | `login_replay` | JSON macro login (incl. optional Playwright step) |
| `captcha_detection` | `captcha` | Detect captcha; skip protected pages |
| `challenge_solver` | `challenge_solver` | CF/Akamai solve via Playwright |
| `intercepting_proxy` | `intercepting_proxy` | mitmweb subprocess |
| `browser_automation` | `advanced.enable_javascript_rendering` | Playwright smart tests |
| `payload_obfuscation` | payload config | WAF encoding helpers |

## AI & intelligence

| Package | Config key | Description |
|---------|------------|-------------|
| `ai_triage` | `ai_triage` / `bug_bounty` | FP scoring + bounty MD |
| `ai_planner` | `ai_planner` | Check order + budget after recon |
| `evidence_summary` | `evidence_summary` | Per-finding LLM bullets |
| `fp_replay` | `fp_replay` | Re-probe triage FPs |
| `cve_intelligence` | `rag`, `experimental` | CVE DB, matcher, RAG index |
| `template_engine` | `templates` | Nuclei-style YAML execution |
| `ml_detection` | `ml_detection` / `anomaly_detector` | Anomaly detector |

## Collaboration & reporting helpers

| Package | Config | Description |
|---------|--------|-------------|
| `collaboration` | `collaboration` | Team session helper (library-style) |
| `reporting` | — | Interactive report helper (demo path) |

---

## How modules are wired

| Path | Modules |
|------|---------|
| `VulnerabilityScanner` imports + `scan()` | Classic set (api, auth, nosql, …) |
| `VulnerabilityScanner._feature_testers` | cors_csp, jwt_deep, graphql_deep, idor, stored_xss, email_injection, cache_deception, h2_smuggle, supply_chain_js, waf_fingerprint, ssrf_cloud, host_header_deep, hpp_pollution, open_redirect_deep, crlf_header_inject_deep, ssti_engines, http_method_override, api_bola_deep, websocket_deep, sse_injection, cloud_misconfig, php_webshell, frida_mobile, android_static, ios_plist, mobile_ssl_pinning, mobile_ai_chain |
| `ScannerEngine._init_extra_module_testers` | directory_bruteforce, port_scanner, saml_attacks, subdomain_takeover, cache_poisoning |
| `ScannerEngine` lifecycle | recon, browser, secrets, templates, challenge, login, captcha, proxy, OAST, OpenAPI, planner, dedupe, FP replay, evidence, RAG, compliance, triage |

---

## Adding a module

1. Create `modules/<name>/__init__.py` + tester  
2. Implement `(http_client, config)` + `scan(url, context=None)`  
3. Append to `_feature_testers` **or** `_init_extra_module_testers`  
4. Add check name under `enabled_checks` in `config/config.example.yaml`  
5. Add a small test under `tests/` when practical  

Do **not** invent nonstandard result keys that break export/diff.

## Related

- [CONFIGURATION.md](CONFIGURATION.md)  
- [ARCHITECTURE.md](ARCHITECTURE.md)  
- [SCAN_FLOW.md](SCAN_FLOW.md)  
