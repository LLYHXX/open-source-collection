# TESTS

## OVERVIEW
pytest suite; flat `tests/`. Bootstrap: `sys.path.insert` to repo root.

## KEY FILES
| File | Covers |
|------|--------|
| `test_features_1_19.py` | Dedupe, NL scope, OpenAPI, feature modules, planner |
| `test_bugfix_gaps.py` | Remediation keys, gemini kwargs, plugins, OAST URL |
| `test_export_formats.py` | JUnit/CSV/XLSX |
| `test_scan_diff.py` | Diff engine |
| `test_template_engine.py` | Nuclei YAML |
| `test_ai_triage.py` | Triage/bounty |
| `e2e_litellm.py` | Live API script (not pure unit) |

## COMMANDS
```bash
pip install -r requirements-dev.txt
pytest
pytest tests/test_features_1_19.py -v
```

## NOTES
- Prefer mock HTTP; optional deps use skip patterns
- Expand core coverage when editing engine/scanner
