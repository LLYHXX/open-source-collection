"""HTTP Parameter Pollution (HPP) tester.

Differential strategy:
1. Baseline GET with original query string.
2. Probe GET with a single high-value parameter replaced by a sentinel.
3. Polluted GET with duplicate parameters (param=val1&param=val2).

Flag when the polluted response differs from both baseline and probe,
suggesting the backend parsed duplicates as concatenation, array, or last-wins.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

_SENTINEL = "HPP_PROBE_42"


class HPPTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config
        self.max_params = int(config.get("hpp_pollution", {}).get("max_params", 5))
        self.json_probe = bool(config.get("hpp_pollution", {}).get("json_probe", True))

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)

        if qs:
            # Baseline
            baseline_resp = self.http_client.get(url)
            if not baseline_resp:
                return vulns
            baseline_body = (getattr(baseline_resp, "text", "") or "")
            baseline_status = getattr(baseline_resp, "status_code", 0)

            params = list(qs.keys())[: self.max_params]
            for param in params:
                original_vals = qs[param]
                if not original_vals:
                    continue
                original = original_vals[0]

                # Probe: single sentinel value
                probe_qs = {k: list(v) for k, v in qs.items()}
                probe_qs[param] = [_SENTINEL]
                probe_url = urlunparse(
                    parsed._replace(query=urlencode(probe_qs, doseq=True))
                )
                try:
                    probe_resp = self.http_client.get(probe_url)
                except Exception as e:
                    logger.debug(f"HPP probe failed for {param}: {e}")
                    continue
                if not probe_resp:
                    continue
                probe_body = (getattr(probe_resp, "text", "") or "")

                # Polluted: duplicate parameters
                polluted_qs = {k: list(v) for k, v in qs.items()}
                polluted_qs[param] = [original, _SENTINEL]
                polluted_url = urlunparse(
                    parsed._replace(query=urlencode(polluted_qs, doseq=True))
                )
                try:
                    polluted_resp = self.http_client.get(polluted_url)
                except Exception as e:
                    logger.debug(f"HPP polluted failed for {param}: {e}")
                    continue
                if not polluted_resp:
                    continue
                polluted_body = (getattr(polluted_resp, "text", "") or "")
                polluted_status = getattr(polluted_resp, "status_code", 0)

                if polluted_body != baseline_body:
                    # Try to infer backend behavior from body
                    behavior = self._infer_behavior(polluted_body, probe_body, original, _SENTINEL)
                    vulns.append(
                        {
                            "type": "HTTP Parameter Pollution",
                            "severity": "medium",
                            "url": polluted_url,
                            "parameter": param,
                            "payload": f"{param}={original}&{param}={_SENTINEL}",
                            "evidence": (
                                f"status={polluted_status} "
                                f"behavior={behavior} "
                                f"len_baseline={len(baseline_body)} "
                                f"len_probe={len(probe_body)} "
                                f"len_polluted={len(polluted_body)}"
                            ),
                            "description": (
                                f"Duplicate parameter '{param}' produced a response "
                                f"different from baseline. "
                                f"Backend likely parsed duplicates as: {behavior}."
                            ),
                            "remediation": (
                                "Normalize parameter parsing (reject duplicates, pick first, "
                                "or explicitly handle arrays) and ensure WAF/policy layer "
                                "agrees with application-layer parsing."
                            ),
                        }
                    )

        # Optional JSON duplicate-key probe
        if self.json_probe and context and context.get("content_type", "").startswith(
            "application/json"
        ):
            json_vulns = self._json_duplicate_probe(url, context)
            vulns.extend(json_vulns)

        return vulns

    @staticmethod
    def _infer_behavior(polluted_body: str, probe_body: str, original: str, sentinel: str) -> str:
        if original + sentinel in polluted_body or sentinel + original in polluted_body:
            return "concatenation"
        if f'["{original}", "{sentinel}"]' in polluted_body or f'["{sentinel}", "{original}"]' in polluted_body:
            return "array"
        if polluted_body == probe_body:
            return "last-wins"
        if original in polluted_body and sentinel not in polluted_body:
            return "first-wins"
        return "unknown"

    def _json_duplicate_probe(self, url: str, context: Dict) -> List[Dict]:
        vulns: List[Dict] = []
        body_data = context.get("body")
        if not body_data:
            return vulns
        try:
            parsed_json = json.loads(body_data) if isinstance(body_data, str) else body_data
        except Exception:
            return vulns
        if not isinstance(parsed_json, dict):
            return vulns

        for key in list(parsed_json.keys())[: self.max_params]:
            dup = {**parsed_json, key: "HPP_JSON_PROBE"}
            try:
                resp = self.http_client.post(
                    url,
                    data=json.dumps(dup),
                    headers={"Content-Type": "application/json"},
                )
            except Exception as e:
                logger.debug(f"HPP JSON probe failed for {key}: {e}")
                continue
            if not resp:
                continue
            resp_body = (getattr(resp, "text", "") or "")
            if "HPP_JSON_PROBE" in resp_body:
                vulns.append(
                    {
                        "type": "HTTP Parameter Pollution (JSON duplicate key)",
                        "severity": "medium",
                        "url": url,
                        "parameter": key,
                        "payload": json.dumps(dup),
                        "evidence": f"Duplicate JSON key '{key}' reflected in response",
                        "description": (
                            f"Duplicate JSON key '{key}' was accepted and its value "
                            f"appeared in the response, indicating parser-dependent behavior."
                        ),
                        "remediation": (
                            "Reject duplicate keys in JSON parser or define explicit "
                            "merge/overwrite semantics at the application layer."
                        ),
                    }
                )
        return vulns
