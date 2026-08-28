# EXPORTS MODULE

**Scope:** JUnit XML, CSV, XLSX, and diff renderers for scan results.

## OVERVIEW
Pure builder functions that turn vulnerability result lists into bytes or strings.
Called by `ReportGenerator` (post-scan) and `core/scan_diff.py` (`--diff` mode).
No I/O here; callers handle file writes.

## STRUCTURE
```
utils/exports/
├── __init__.py        # Re-exports build_*; __all__ is the registry
├── junit_builder.py   # build_junit_xml(results) -> str
├── csv_builder.py     # build_csv(results) -> str
├── xlsx_builder.py    # build_xlsx(results) -> bytes
└── diff_renderer.py   # render_html/json/csv for scan diffs
```

## WHERE TO LOOK
| Task | File | Notes |
|------|------|-------|
| Add export format | New `*_builder.py` + `__init__.py` | Must return bytes or str |
| Diff reports | `diff_renderer.py` | Used by `--diff` and `scan_diff.py` |
| Format tests | `tests/test_export_formats.py` | All builders |
| Diff tests | `tests/test_scan_diff.py` | Diff renderer coverage |

## CONVENTIONS
- Builder signature: `build_<format>(results: List[Dict]) -> Union[str, bytes]`.
- Register in `__init__.__all__` or ReportGenerator will not discover it.
- Input dicts use standard vuln keys: `type`, `severity`, `url`, `parameter`, `evidence`.
- Keep dependencies minimal; xlsx uses `openpyxl`, junit uses stdlib `xml.etree`.

## ANTI-PATTERNS
- Do not open/write files inside builders; return data only.
- Do not add side effects (logging, HTTP calls, DB reads).
- Do not skip `__all__` registration for new builders.
- Do not invent new vuln result keys; stick to the standard dict shape.
