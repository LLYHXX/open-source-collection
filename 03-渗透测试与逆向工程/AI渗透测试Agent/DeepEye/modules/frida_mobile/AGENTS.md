# MOBILE / FRIDA

## OVERVIEW
Static + dynamic mobile helpers. Frida scripts generated offline; live attach optional.

## MODULES
| Package | Role |
|---------|------|
| `frida_mobile` | Write Frida JS hooks; AI payload advice + attack chain |
| `android_static` | APK zip heuristics (debuggable, backup, secrets) |
| `ios_plist` | Info.plist ATS + URL schemes |
| `mobile_ssl_pinning` | Detect pinning indicators |
| `mobile_ai_chain` | Ordered attack chain + suggested payloads (AI optional) |

## ENABLE
```yaml
mobile:
  enabled: true
  platform: android   # or ios
  package: com.example.app
  artifact: path/to/app.apk
  use_ai: true
  script_output_dir: reports/frida_scripts
  try_attach: false

vulnerability_scanner:
  enabled_checks:
    - frida_mobile
    - android_static
    - ios_plist
    - mobile_ssl_pinning
    - mobile_ai_chain
```

## AI
- `set_ai_manager` injected from ScannerEngine for Frida + mobile_ai_chain.
- Without AI: heuristic chain/payloads still returned.
- With AI: JSON hooks/payloads/attack_chain merged into findings (`ai_payload_advice`, `attack_chain`).

## VERIFY
```bash
pytest tests/test_mobile_frida.py -v
```
