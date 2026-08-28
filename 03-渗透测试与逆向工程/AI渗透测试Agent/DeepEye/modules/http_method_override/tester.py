"""HTTP Method Override tester.

Strategy:
1. Send a real DELETE (or PATCH/PUT) to the URL.
2. If it returns 405 Method Not Allowed, the endpoint is interesting.
3. Replay the same URL with X-HTTP-Method-Override (and variants) set to
   DELETE/PATCH/PUT on a GET or POST request.
4. Flag if the override request returns 200/204/302 — the server honored
   the override header and executed the restricted method.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

_OVERRIDES = [
    "X-HTTP-Method-Override",
    "X-HTTP-Method",
    "X-METHOD-OVERRIDE",
    "_method",
]

_METHODS = ["DELETE", "PATCH", "PUT"]

_SUCCESS_STATUSES = {200, 201, 202, 204, 302, 303, 307, 308}


class HTTPMethodOverrideTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config
        self.probe_methods = config.get("http_method_override", {}).get(
            "probe_methods", _METHODS
        )
        self.override_headers = config.get("http_method_override", {}).get(
            "override_headers", _OVERRIDES
        )

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []

        # Test each restricted method
        for method in self.probe_methods:
            try:
                real_resp = self._request(url, method)
            except Exception as e:
                logger.debug(f"Method override real {method} failed: {e}")
                continue
            if not real_resp:
                continue
            real_status = getattr(real_resp, "status_code", 0)

            # Only interesting if real method is blocked (405) or we can't tell
            if real_status not in (405, 403, 501, 502):
                # If the real method already works, no override bypass to report
                continue

            # Try override via GET and POST carriers
            for carrier in ("GET", "POST"):
                for header in self.override_headers:
                    try:
                        resp = self._request(url, carrier, headers={header: method})
                    except Exception as e:
                        logger.debug(f"Method override {carrier}/{header}={method}: {e}")
                        continue
                    if not resp:
                        continue
                    status = getattr(resp, "status_code", 0)
                    if status in _SUCCESS_STATUSES:
                        vulns.append(
                            {
                                "type": "HTTP Method Override Bypass",
                                "severity": "high",
                                "url": url,
                                "parameter": "method",
                                "payload": f"{carrier} + {header}: {method}",
                                "evidence": (
                                    f"Real {method} returned {real_status}; "
                                    f"override via {carrier} with {header} returned {status}"
                                ),
                                "description": (
                                    f"Endpoint blocked real {method} ({real_status}) but "
                                    f"accepted it via {header} on a {carrier} request, "
                                    f"returning {status}. This may allow unauthorized "
                                    f"destructive or state-changing operations."
                                ),
                                "remediation": (
                                    "Validate the actual HTTP method at the application "
                                    "layer; do not trust X-HTTP-Method-Override or similar "
                                    "headers for authorization decisions."
                                ),
                            }
                        )
                        # One finding per method is enough
                        return vulns
        return vulns

    def _request(self, url: str, method: str, headers: Optional[Dict] = None):
        m = method.upper()
        if m == "GET":
            return self.http_client.get(url, headers=headers)
        if m == "POST":
            return self.http_client.post(url, data="", headers=headers)
        if m == "DELETE":
            return self.http_client.delete(url, headers=headers)
        if m == "PUT":
            return self.http_client.put(url, data="", headers=headers)
        if m == "PATCH":
            return self.http_client.patch(url, data="", headers=headers)
        # Fallback for unknown methods
        return self.http_client.request(m, url, headers=headers)
