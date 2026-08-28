# AI TRIAGE MODULE

**Generated:** 2026-07-15
**Scope:** False-positive filtering + bug bounty report generation

## OVERVIEW
Post-scan AI review. `AITriage` scores each finding for confidence and false-positive likelihood. `BountyWriter` generates per-vuln Markdown reports. Both run in `ScannerEngine` after RAG/compliance enrichment, before the final report. Operates on the results list in-place, can drop entries.

## STRUCTURE
```
modules/ai_triage/
├── triage.py          # AITriage class
├── bounty_writer.py   # BountyWriter class
└── prompts.py         # TRIAGE_PROMPT, BOUNTY_PROMPT
```

## WHERE TO LOOK
| Task | File | Notes |
|------|------|-------|
| FP filtering | `triage.py` | `_triage_one`, `_parse_ai_json`, `triage_vulnerabilities` |
| Bounty reports | `bounty_writer.py` | `_generate_one`, `generate_reports`, `_slugify` |
| Prompt text | `prompts.py` | JSON triage prompt + Markdown bounty prompt |
| Integration | `core/scanner_engine.py` | Called after RAG/compliance, before `ReportGenerator` |
| Tests | `tests/test_ai_triage.py` | MockAI-based unit tests |

## CONVENTIONS
- Config keys: `ai_triage.enabled`, `drop_false_positives`, `drop_threshold`, `min_severity`; `bug_bounty.enabled`, `format`, `output_directory`.
- `ai_manager.generate(prompt)` via LiteLLM-capable stack. Failures are caught, logged, and treated as low-confidence / no-bounty.
- `_parse_ai_json` tolerates code fences and prose. Malformed responses get confidence 0.4 and kept.
- `SEVERITY_RANK` shared between triage and bounty writer for consistent filtering.
- `triage_vulnerabilities` mutates the list in-place. `drop_fps` rebuilds the list, discarding high-confidence FPs.
- Bounty writer skips `false_positive=True` vulns regardless of severity.

## ANTI-PATTERNS
- Do not crash the scan if the AI provider fails. Both classes catch exceptions and degrade gracefully.
- Do not drop FPs below `drop_threshold`. Borderline cases stay in the results for human review.
- Do not write bounty files when `one_file_per_vuln` is false. Only attach `bounty_report` to the dict.
- Do not invent new severity strings. Use the same `critical|high|medium|low|info` scale as the rest of the scanner.
