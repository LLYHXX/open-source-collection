# Deep Eye Skills (`.agents/skills`)

On-demand Markdown skills for agents. Loader: `proxy/system.py` → `<available_skills>`.

## Layout

| Path | Purpose |
|------|---------|
| `pentest/`, `bug-bounty/`, `red-team/`, `blue-team/`, `ctf/`, `security-ops/` | Workflow skills (`SKILL.md`) |
| `vulnerabilities/` | Vuln-class playbooks |
| `reconnaissance/` | Recon SOP |
| `protocols/` | GraphQL etc. |
| `payloads/` | Short payload packs |
| `tools/` | Deep Eye CLI / browser |
| `technologies/` | Cloud etc. |
| `frameworks/` | Next.js etc. |

## Format

Follow `docs/create_skills_rules.md` template: Trigger, Overview, Detection, Checklist, Payloads, Tools, Exploitation, Bypasses, Remediation.

## Load

```python
from proxy.system import get_system_prompt, list_skill_index, read_skill
print(list_skill_index())
print(read_skill("sql_injection")[:200])
```

## Rules

Authorized targets only. One vuln class per file. Exact Deep Eye commands.
