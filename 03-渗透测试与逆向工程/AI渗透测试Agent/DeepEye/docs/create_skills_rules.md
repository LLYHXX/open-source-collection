# Skills System — Complete Guide

## Table of Contents

1. [What are Skills?](#1-what-are-skills)
2. [How Skills Work Internally](#2-how-skills-work-internally)
3. [Available Skills Reference](#3-available-skills-reference)
4. [deep-eye-skills Community Library](#4-deep-eye-skills-community-library)
5. [Creating a Custom Skill](#5-creating-a-custom-skill)
6. [Skill Writing Guidelines](#6-skill-writing-guidelines)
7. [Full Skill Template](#7-full-skill-template)
8. [Testing Your Skill](#8-testing-your-skill)

---

## 1. What are Skills?

Skills are plain Markdown (`.md`) files stored in **`deep-eye/.agents/skills/`** (canonical). They contain specialized knowledge about attack techniques, tool usage, and testing procedures for specific technologies or vulnerability classes.

> **Note:** Older docs referred to `proxy/skills/`. That path is **legacy**. The loader in `proxy/system.py` reads **`.agents/skills/`** first (and still scans `proxy/skills/` if present).

**Skills complement the system prompt.** The system prompt gives the agent general security methodology. Skills provide deep, specific knowledge on-demand — without bloating the main prompt with information that is irrelevant to most targets.

**Examples of what skills contain:**
- Step-by-step testing checklists for a specific vulnerability (e.g., SQLi, SSRF)
- Exact tool commands for a specific technology (e.g., GraphQL introspection, Firebase rules)
- Payload collections tailored to a specific attack surface
- Knowledge about a specific framework's security model (e.g., Next.js server actions, FastAPI auth)

---

## 2. How Skills Work Internally

### 2.1 Discovery at startup

When skills are requested, `proxy/system.py` scans **`.agents/skills/**/*.md`** and builds a list of absolute paths:

```python
# deep-eye/proxy/system.py
from proxy.system import get_available_skills_block, list_skill_paths
# list_skill_paths() -> .agents/skills/**/*.md (+ legacy proxy/skills if any)
# get_available_skills_block() -> <available_skills> ... paths ...
```

This list is injected into the system prompt as an `<available_skills>` block:

```
<available_skills>
You have access to the following skill documents. If you need specific guidance
on a topic, use the `read_file` tool with the EXACT absolute path listed below:
- /.../deep-eye/.agents/skills/vulnerabilities/xss.md
- /.../deep-eye/.agents/skills/vulnerabilities/sql_injection.md
- /.../deep-eye/.agents/skills/protocols/graphql.md
- /.../deep-eye/.agents/skills/pentest/SKILL.md
...
</available_skills>
```

### 2.2 On-demand loading by the agent

The agent does **not** preload skill content into its context. Skills are loaded on demand using the `read_file` tool:

```
# Agent calls:
read_file(path="/absolute/path/to/skills/vulnerabilities/ssrf.md")
```

The agent decides to read a skill when:
- It detects a relevant technology in scan results (e.g., `whatweb` returns "GraphQL")
- It encounters a vulnerability class it wants detailed guidance on
- The user prompt references a specific topic (e.g., "test for JWT issues")
- A tool output contains keywords that match a skill topic

### 2.3 Why this design?

Loading all skills at startup would consume 50,000+ tokens of context window — wasted on irrelevant content for most targets. On-demand loading means the agent only pays the context cost for skills it actually needs.

---

## 3. Available Skills Reference

### Vulnerabilities (`skills/vulnerabilities/`)

| File | Topic |
|------|-------|
| `api_testing.md` | REST/SOAP/GraphQL parameter discovery, verb tampering, rate limit bypass |
| `authentication_jwt.md` | JWT attacks: alg:none, weak secrets, RS256→HS256 confusion, kid injection |
| `bfla.md` | BFLA / privilege escalation via HTTP method tampering |
| `business_logic.md` | Business logic flaws, 7-step procedure, workflow abuse, state machine attacks |
| `csrf.md` | CSRF bypass techniques: SameSite confusion, token stealing, JSON CSRF, multipart |
| `deserialization.md` | Java gadget chains, PHP object injection, Python pickle, .NET deserialization |
| `exploitation.md` | General exploitation patterns, PoC construction, post-exploitation |
| `grpc.md` | gRPC proto enumeration, reflection API abuse, auth bypass, injection |
| `http_smuggling.md` | CL.TE, TE.CL, TE.TE desync, request tunneling |
| `idor.md` | IDOR discovery and exploitation: numeric, UUID, encoded IDs |
| `information_disclosure.md` | Sensitive data leakage: error messages, debug endpoints, JS secrets |
| `insecure_file_uploads.md` | File upload bypass: extension spoofing, polyglots, path traversal via upload |
| `kubernetes.md` | RBAC misconfig, etcd exposure, container escape, service account abuse |
| `mass_assignment.md` | Mass assignment and parameter pollution attacks |
| `oauth_saml.md` | Authorization code abuse, implicit flow, SAML assertion manipulation |
| `open_redirect.md` | Open redirect detection and OAuth `redirect_uri` abuse |
| `path_traversal.md` | Path traversal, LFI, RFI, PHP wrapper chains, log poisoning |
| `privilege_escalation.md` | Vertical/horizontal privilege escalation, JWT privilege claims, role confusion |
| `prototype_pollution.md` | Client-side and server-side (Node.js), lodash/merge sinks |
| `race_conditions.md` | Race condition testing: limit bypass, TOCTOU, last-write-wins |
| `rce.md` | Remote code execution via SSTI, command injection, deserialization gadgets |
| `sql_injection.md` | SQLi: error-based, blind, time-based, OOB, WAF bypass, SQLMap advanced |
| `ssrf.md` | SSRF: cloud metadata, internal ports, DNS rebinding, protocol wrappers, filter bypass |
| `ssti.md` | SSTI: Jinja2, Twig, Freemarker, Smarty, Pebble template injection |
| `subdomain_takeover.md` | Takeover detection and exploitation for unclaimed DNS/cloud resources |
| `supply_chain.md` | Dependency confusion, typosquatting, malicious package injection |
| `waf_detection.md` | WAF fingerprinting, bypass techniques, encoding evasion |
| `web_cache_poisoning.md` | Header injection, cache key normalization, CPDoS |
| `websocket.md` | WS hijacking, CSWSH, protocol downgrade, message injection |
| `xss.md` | XSS: reflected, stored, DOM-based, mutation, CSP bypass, exfiltration |
| `xxe.md` | XXE: file read, SSRF via DTD, billion laughs, SVG/XLSX vectors |

### Reconnaissance (`skills/reconnaissance/`)

| File | Topic |
|------|-------|
| `full_recon.md` | 19KB Standard Operating Procedure — complete recon workflow with concrete success criteria, tool sequencing, artifact requirements, and phase transition rules |

### Frameworks (`skills/frameworks/`)

| File | Topic |
|------|-------|
| `fastapi.md` | FastAPI security: dependency injection abuse, auth bypass, OpenAPI exposure, validation bypass |
| `nextjs.md` | Next.js security: middleware bypass, server actions, API routes, ISR cache poisoning, SSRF via redirects |

### Technologies (`skills/technologies/`)

| File | Topic |
|------|-------|
| `cloud_security.md` | AWS/GCP/Azure misconfigs: S3 ACLs, IAM privilege escalation, metadata service abuse |
| `firebase_firestore.md` | Firebase security rules testing, unauthenticated access, NoSQL injection |
| `supabase.md` | Supabase RLS bypass, storage misconfigs, service key exposure, API key abuse |

### Protocols (`skills/protocols/`)

| File | Topic |
|------|-------|
| `active_directory.md` | Kerberoasting, AS-REP roasting, BloodHound, lateral movement, DCSync |
| `graphql.md` | GraphQL introspection, injection, batching abuse, IDOR via aliases, DoS |

### Payloads (`skills/payloads/`)

| File | Topic |
|------|-------|
| `command_injection.md` | Command injection payload collection with filter bypass variants |
| `lfi.md` | LFI payload collection: path normalization, PHP wrappers, null bytes |
| `sqli.md` | SQL injection payload collection by database type and technique |
| `ssrf.md` | SSRF payload collection: cloud metadata URLs, protocol wrappers |
| `ssti.md` | SSTI payload collection by template engine |
| `xss.md` | XSS payload collection: filter bypass, DOM sinks, CSP bypass |
| `xxe.md` | XXE payload collection: OOB exfil, DTD injection, SVG/XLSX vectors |

### Tools (`skills/tools/`)

| File | Topic |
|------|-------|
| `advanced_fuzzing.md` | deep-eye fuzzing engine usage: quick_fuzz, advanced_fuzz, deep_fuzz, schemathesis |
| `browser_automation.md` | Playwright browser automation: auth flows, JS execution, network capture |
| `caido.md` | Caido proxy integration: HTTPQL filters, §FUZZ§ markers, automate patterns |
| `dalfox.md` | Dalfox XSS scanner: flags, blind XSS, DOM scan, custom payloads |
| `install.md` | Tool installation procedures for the Kali sandbox |
| `nmap.md` | Nmap usage: script categories, output formats, NSE scripts for web |
| `nuclei.md` | Nuclei templates: custom templates, severity filters, OOB templates |
| `scripting.md` | 81KB scripting guide: Python patterns for HTTP testing, auth, rate limiting |
| `semgrep.md` | Semgrep SAST: custom rules, OWASP rulesets, triage workflow |
| `sqlmap.md` | SQLmap: tamper scripts, blind injection, file read/write, OS shell |
| `tool_catalog.md` | Full catalog of all preinstalled Kali sandbox tools with usage examples |

---

## 4. deep-eye-skills Community Library

**[deep-eye-skills](https://github.com/pikpikcu/deep-eye-skills)** is the official community skill library for deep-eye — a collection of CLI-based playbooks for CTF, bug bounty, and pentesting that extend the built-in skill set.

### What's included

The library provides specialized skills not bundled with deep-eye by default:

| Category | Examples |
|----------|---------|
| CTF | Reverse engineering, binary exploitation, crypto challenges, web CTF |
| Bug Bounty | Platform-specific recon SOPs, disclosure tips, P1 hunting patterns |
| Protocols | MQTT, Redis, MongoDB, Kafka, Elasticsearch attack playbooks |
| Cloud | AWS privilege escalation chains, GCP service account abuse, Azure AD attacks |
| Mobile | Android APK decompile + secrets scan, iOS plist inspection |
| Frameworks | Django, Rails, Spring Boot, Laravel, WordPress deep dives |

### Installation

```text
# Clone into your local skills directory
git clone https://github.com/pikpikcu/deep-eye-skills ~/.deep-eye/skills

# Or clone alongside the built-in skills
git clone https://github.com/pikpikcu/deep-eye-skills /path/to/deep-eye-skills
```

Then configure deep-eye to load skills from the additional directory by setting the path in your config or by symlinking into the built-in skills folder:

```text
# Option 1: Symlink into project skills (recommended)
# Linux/macOS:
ln -s ~/.deep-eye/skills/skills/* /path/to/deep-eye/.agents/skills/
# Windows (Admin or Developer Mode):
# New-Item -ItemType SymbolicLink -Path .agents\skills\ctf-extra -Target $HOME\.deep-eye\skills\skills\ctf

# Option 2: Copy skills you want
cp -r ~/.deep-eye/skills/skills/ctf /path/to/deep-eye/.agents/skills/
```

After adding skills, restart deep-eye — they will appear automatically in `<available_skills>`.

### Verifying community skills are loaded

```text
python3 -c "
from deep-eye.proxy.system import get_system_prompt
p = get_system_prompt()
start = p.find('<available_skills>')
end = p.find('</available_skills>') + len('</available_skills>')
print(p[start:end])
" | grep -i ctf  # or whatever category you added
```

### Contributing to deep-eye-skills

If you write a skill that could be useful to others, consider contributing it upstream:

1. Fork [github.com/pikpikcu/deep-eye-skills](https://github.com/pikpikcu/deep-eye-skills)
2. Add your skill in the appropriate category folder
3. Follow the [Skill Writing Guidelines](#6-skill-writing-guidelines) below
4. Open a pull request

---

## 5. Creating a Custom Skill

### Step 1: Choose the right location

**Built-in skills** (ship with deep-eye): add to `deep-eye/.agents/skills/<category>/`

**Workflow skills** (pentest/bounty/red/blue/ctf): `deep-eye/.agents/skills/<name>/SKILL.md`

**Community skills** (deep-eye-skills library): contribute to [github.com/pikpikcu/deep-eye-skills](https://github.com/pikpikcu/deep-eye-skills)

**Private skills** (your own): place under `.agents/skills/` or symlink into it.

### Step 2: Choose the right category

| Your skill is about... | Folder |
|-----------------------|--------|
| A specific vulnerability class | `.agents/skills/vulnerabilities/` |
| A web framework | `.agents/skills/frameworks/` |
| A backend technology or SaaS | `.agents/skills/technologies/` |
| A protocol (GraphQL, WebSocket, gRPC, AD) | `.agents/skills/protocols/` |
| Recon methodology / SOP | `.agents/skills/reconnaissance/` |
| Payload collections | `.agents/skills/payloads/` |
| Tool usage guide | `.agents/skills/tools/` |
| Engagement workflow | `.agents/skills/pentest/` (etc.) |

### Step 3: Create the file

```text
# Example: adding a WebSocket testing skill
# (Windows PowerShell)
New-Item -Force .agents/skills/protocols/websocket.md
```

### Step 4: Write the skill (see [Full Template](#7-full-skill-template) below)

### Step 5: Restart deep-eye

Skills are scanned at startup. Restart for the new file to appear in the `<available_skills>` list.

```text
# Stop current session and restart
deep-eye start
```

### Step 6: Verify

Ask the agent to check a relevant target. When it detects the relevant technology, it should read your skill. You can also manually trigger it:

```
# In the TUI, type:
read the websocket skill and test this target for WebSocket vulnerabilities
```

---

## 6. Skill Writing Guidelines

### DO: Be specific and actionable

```markdown
# Good
Run: `python3 /home/pentester/tools/jwt_tool/jwt_tool.py <token> -X a`
This tests the alg:none bypass — if it succeeds, the server accepts unsigned tokens.

# Bad
"Test the JWT implementation for common vulnerabilities."
```

### DO: Include exact commands with real flags

```markdown
# Good
`subfinder -d <target> -all -recursive -o output/subdomains.txt`

# Bad
"Use subfinder to find subdomains."
```

### DO: Explain what success looks like

```markdown
**Success indicator:** Response changes from 403 to 200, or user data from a different account appears in the response body.
```

### DO: Keep payloads focused — 5 representative ones, not 50

```markdown
# Good (5 payloads covering different bypass patterns)
```sql
' OR 1=1--
' OR '1'='1
admin'--
' UNION SELECT NULL--
1; DROP TABLE users--
```

### DON'T: Write generic advice

```markdown
# Bad — this is already in the system prompt
"Test all endpoints for injection vulnerabilities."
```

### DON'T: Add lengthy prose explanations

Skills go into context window. Every word costs tokens. If something is already covered by general security knowledge, skip it.

### DON'T: Add more than one vulnerability class per file

Split `sql_and_nosql_injection.md` into `sql_injection.md` and `nosql_injection.md`. The agent searches for specific skills — mixing topics makes skills harder to locate and use efficiently.

---

## 7. Full Skill Template

```markdown
# <Skill Name>

**Trigger condition:** <When should the agent load this skill? What observation in scan output indicates this skill is relevant?>

## Overview
<2–3 sentences max. What is this vulnerability/technology and why does it matter for security testing?>

## Detection
How to confirm the target uses this technology or is affected:

```text
# Detection command 1
<exact command>

# Detection command 2
<exact command>
```

**Indicators in tool output:**
- `<string or pattern to look for in httpx/nuclei/browser output>`
- `<another indicator>`

## Testing Checklist

### Test 1: <Name>
**Tool:** `<command with exact flags>`
**What to look for:** `<success indicator>`

### Test 2: <Name>
**Tool:** `<command>`
**What to look for:** `<success indicator>`

### Test 3: <Name> (Manual)
1. `<step 1>`
2. `<step 2>`
3. `<expected result>`

## Key Payloads

```
<payload 1 — covers bypass pattern A>
<payload 2 — covers bypass pattern B>
<payload 3 — WAF evasion variant>
```

## Tools Available

| Tool | Command | Purpose |
|------|---------|---------|
| `<tool>` | `<exact invocation>` | <one-line purpose> |
| `python3 /home/pentester/tools/<t>/<s>.py` | `<args>` | <purpose> |

## Exploitation (When Vulnerability is Confirmed)

1. Document: capture the exact request/response pair demonstrating impact
2. Prove impact: `<exact command or payload that demonstrates damage>`
3. Report: call `create_vulnerability_report` with:
   - `poc_script_code`: working Python script that reproduces the issue
   - `impact`: exact data accessed or action taken

## Common Bypasses

- **WAF filter:** `<bypass technique>`
- **Encoding:** `<alternative encoding>`
- **Edge case:** `<less-obvious variant>`

## Remediation Summary
- <Fix point 1>
- <Fix point 2>
```

---

## 8. Testing Your Skill

After creating a skill, verify it works as expected:

**1. Check it appears in the skill list:**

```text
# From repo root
python -c "
from proxy.system import get_system_prompt, list_skill_index
print(list_skill_index()[:20])
p = get_system_prompt()
start = p.find('<available_skills>')
end = p.find('</available_skills>') + len('</available_skills>')
print(p[start:end][:1500])
"
```

**2. Resolve a skill path:**

```text
python -c "
from proxy.system import find_skill, read_skill
print(find_skill('sql_injection'))
print(read_skill('sql_injection')[:400])
"
```

**3. Unit tests:**

```text
pytest tests/test_proxy_skills.py -q
```

If the path is listed in `<available_skills>` and `read_skill` returns content, the skill is working.