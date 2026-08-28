"""HTTP/2 / h2c and classic CL.TE smuggling probes (safe heuristics)."""
from __future__ import annotations

from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class H2SmuggleTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []
        # h2c upgrade probe
        try:
            resp = self.http_client.get(
                url,
                headers={
                    "Connection": "Upgrade, HTTP2-Settings",
                    "Upgrade": "h2c",
                    "HTTP2-Settings": "AAMAAABkAARAAAAAAAIAAAAA",
                },
            )
            if resp is not None:
                st = getattr(resp, "status_code", 0)
                h = {k.lower(): v for k, v in dict(resp.headers).items()}
                if st == 101 or "h2" in str(h.get("upgrade", "")).lower():
                    vulns.append(
                        {
                            "type": "HTTP/2 Cleartext Upgrade (h2c) Enabled",
                            "severity": "medium",
                            "url": url,
                            "parameter": "Upgrade",
                            "payload": "h2c",
                            "evidence": f"HTTP {st} upgrade={h.get('upgrade')}",
                            "description": "h2c upgrade accepted — review proxy desync risk",
                            "remediation": "Disable h2c on edge unless required; normalize HTTP/1.1 vs h2",
                        }
                    )
        except Exception as e:
            logger.debug(f"h2c probe: {e}")

        # Conflicting length headers (request may be blocked by client lib — still try)
        try:
            resp = self.http_client.get(
                url,
                headers={
                    "Content-Length": "4",
                    "Transfer-Encoding": "chunked",
                },
            )
            if resp is not None and getattr(resp, "status_code", 0) not in (400, 501):
                # soft signal only
                vulns.append(
                    {
                        "type": "HTTP Smuggling Header Ambiguity",
                        "severity": "info",
                        "url": url,
                        "parameter": "Transfer-Encoding",
                        "payload": "CL + TE both set",
                        "evidence": f"Server responded {getattr(resp, 'status_code', '?')} to ambiguous headers",
                        "description": "Server accepted request with CL+TE; verify desync with dedicated tools",
                        "remediation": "Reject ambiguous Content-Length / Transfer-Encoding combinations",
                    }
                )
        except Exception as e:
            logger.debug(f"CL.TE probe: {e}")
        return vulns
