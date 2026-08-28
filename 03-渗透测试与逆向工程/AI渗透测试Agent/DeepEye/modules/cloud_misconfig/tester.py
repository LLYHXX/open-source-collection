"""Cloud misconfiguration probes: metadata, storage buckets, takeovers lite."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import urlparse

from utils.logger import get_logger

logger = get_logger(__name__)

_META = [
    ("aws_imds", "http://169.254.169.254/latest/meta-data/", ["ami-id", "instance-id", "iam"]),
    ("aws_imds_token", "http://169.254.169.254/latest/api/token", ["X-aws", "token"]),
    ("gcp", "http://metadata.google.internal/computeMetadata/v1/project/project-id", ["project", "compute"]),
    ("azure", "http://169.254.169.254/metadata/instance?api-version=2021-02-01", ["compute", "vmId", "subscriptionId"]),
]

_BUCKET_TMPL = [
    "https://{host}.s3.amazonaws.com",
    "https://s3.amazonaws.com/{host}",
    "https://{host}.s3.amazonaws.com/robots.txt",
    "https://storage.googleapis.com/{host}",
    "https://{host}.blob.core.windows.net",
]


class CloudMisconfigTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("cloud_misconfig") or {}
        self.probe_metadata = bool(self.cfg.get("probe_metadata_via_ssrf_params", True))

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        context = context or {}
        vulns: List[Dict] = []
        host = (urlparse(url).hostname or "").split(":")[0]
        # public bucket name guesses from host
        base = host.split(".")[0] if host else ""
        names = {base, host.replace(".", "-"), host.replace(".", "")}
        names = {n for n in names if n and len(n) > 2}

        for name in list(names)[:5]:
            for tmpl in _BUCKET_TMPL:
                bucket_url = tmpl.format(host=name)
                try:
                    resp = self.http_client.get(bucket_url)
                    if not resp:
                        continue
                    st = getattr(resp, "status_code", 0)
                    body = (getattr(resp, "text", "") or "")[:1500]
                    if st == 200 and any(
                        x in body for x in ("ListBucketResult", "Blob", "Contents", "<Key>", "<?xml")
                    ):
                        vulns.append({
                            "type": "Cloud Storage Bucket Public Listing",
                            "severity": "high",
                            "url": bucket_url,
                            "parameter": "bucket",
                            "payload": name,
                            "evidence": f"HTTP {st}; listing-like XML/body",
                            "description": "Cloud storage bucket appears publicly listable",
                            "remediation": "Block public ACLs; enable block public access; use signed URLs",
                        })
                    elif st in (200, 403) and "NoSuchBucket" not in body and "Not Found" not in body:
                        if "AccessDenied" in body or st == 403:
                            vulns.append({
                                "type": "Cloud Storage Bucket Exists",
                                "severity": "info",
                                "url": bucket_url,
                                "parameter": "bucket",
                                "payload": name,
                                "evidence": f"HTTP {st}",
                                "description": "Bucket name resolves (may be private)",
                                "remediation": "Confirm bucket ownership and access policies",
                            })
                except Exception as e:
                    logger.debug(f"bucket probe: {e}")

        # metadata via query param SSRF-style if URL has params
        if self.probe_metadata_via_params(url):
            from urllib.parse import parse_qs, urlencode, urlunparse

            parsed = urlparse(url)
            qs = parse_qs(parsed.query, keep_blank_values=True)
            if qs:
                key = list(qs.keys())[0]
                for label, meta_url, indicators in _META:
                    try:
                        qs2 = {k: list(v) for k, v in qs.items()}
                        qs2[key] = [meta_url]
                        test = urlunparse(parsed._replace(query=urlencode(qs2, doseq=True)))
                        headers = {}
                        if label == "gcp":
                            headers["Metadata-Flavor"] = "Google"
                        if label == "azure":
                            headers["Metadata"] = "true"
                        resp = self.http_client.get(test, headers=headers or None)
                        if not resp:
                            continue
                        body = getattr(resp, "text", "") or ""
                        if any(i.lower() in body.lower() for i in indicators if len(i) > 2):
                            vulns.append({
                                "type": f"Cloud Metadata Exposure via SSRF ({label})",
                                "severity": "critical",
                                "url": url,
                                "parameter": key,
                                "payload": meta_url,
                                "evidence": body[:200],
                                "description": "Application fetched cloud metadata through user-controlled URL",
                                "remediation": "Block link-local/metadata IPs; IMDSv2; egress controls",
                            })
                            break
                    except Exception as e:
                        logger.debug(f"meta ssrf: {e}")
        return vulns

    def probe_metadata_via_params(self, url: str) -> bool:
        return self.probe_metadata and "?" in url
