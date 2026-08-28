# Deep Eye Skills

Skills are plain Markdown under **`.agents/skills/`**, discovered by `proxy/system.py` and listed in `<available_skills>` for **on-demand** loading.

## Layout

| Path | Purpose |
|------|---------|
| `pentest/`, `bug-bounty/`, `red-team/`, `blue-team/`, `ctf/`, `security-ops/` | Workflow `SKILL.md` |
| `vulnerabilities/` | Vuln-class playbooks (template format) |
| `reconnaissance/` | Recon SOP |
| `protocols/` | GraphQL etc. |
| `payloads/` | Short payload packs |
| `tools/` | Deep Eye CLI / browser |
| `technologies/`, `frameworks/` | Cloud / framework notes |

## Loader

```python
from proxy.system import get_system_prompt, list_skill_index, read_skill
print(list_skill_index())
print(read_skill("sql_injection")[:300])
```

## Format

See [create_skills_rules.md](create_skills_rules.md).

## Rules

Authorized targets only. One vuln class per file. Exact Deep Eye commands.

## Related

CONFIGURATION.md, MODULES.md, AGENTS.md, CLAUDE.md
