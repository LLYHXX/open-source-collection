# Cloud Misconfig / Metadata

**Trigger condition:** Cloud-hosted apps; SSRF possible; checks `ssrf_cloud`, `cloud_misconfig`.

## Overview
Public buckets and SSRF-to-metadata are high-impact cloud findings.

## Detection
```text
# ssrf_cloud, cloud_misconfig
python deep_eye.py -u <target>
```

## Testing Checklist

### Test 1: Metadata SSRF
**Tool:** `ssrf_cloud`
**What to look for:** ami-id / tokens

### Test 2: Bucket listing
**Tool:** `cloud_misconfig`
**What to look for:** ListBucketResult / public list

## Key Payloads
```
http://169.254.169.254/latest/meta-data/
http://metadata.google.internal/computeMetadata/v1/
```

## Tools Available
| Tool | Command | Purpose |
|------|---------|---------|
| Deep Eye | `ssrf_cloud`, `cloud_misconfig` | Cloud probes |

## Exploitation
Prove metadata/bucket access in scope only.

## Common Bypasses
IP encoding, DNS tricks (see ssrf skill)

## Remediation Summary
- Block metadata path from app egress
- Bucket public access blocks
