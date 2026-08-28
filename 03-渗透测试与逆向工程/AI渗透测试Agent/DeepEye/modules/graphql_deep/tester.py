"""GraphQL deep: batching, aliases, depth, introspection, variables inject."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

_INTROSPECTION = {
    "query": "query IntrospectionQuery { __schema { queryType { name } types { name kind } } }"
}

_VAR_INJECT = [
    {
        "query": "query($q:String){ __typename }",
        "variables": {"q": "' OR 1=1--"},
    },
    {
        "query": "query($id:ID!){ __typename }",
        "variables": {"id": "1 OR 1=1"},
    },
    {
        "query": "query($x:String){ __typename }",
        "variables": {"x": "<script>alert(1)</script>"},
    },
    {
        "query": "query($u:String){ __typename }",
        "variables": {"u": "http://169.254.169.254/latest/meta-data/"},
    },
]


class GraphQLDeepTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        if not self._looks_graphql(url, context):
            return []
        vulns: List[Dict] = []
        vulns.extend(self._introspection(url))
        vulns.extend(self._batch(url))
        vulns.extend(self._aliases(url))
        vulns.extend(self._circular(url))
        vulns.extend(self._variables(url))
        vulns.extend(self._field_suggestion(url))
        return vulns

    def _looks_graphql(self, url: str, context: Optional[Dict]) -> bool:
        u = url.lower()
        if "graphql" in u or u.endswith("/gql") or u.endswith("/graphiql"):
            return True
        body = ""
        if context and context.get("response") is not None:
            body = (getattr(context["response"], "text", "") or "")[:2000].lower()
        return "graphql" in body or "__schema" in body or "graphiql" in body

    def _post(self, url: str, payload) -> Optional[object]:
        try:
            return self.http_client.post(url, json=payload)
        except Exception as e:
            logger.debug(f"GraphQL post failed: {e}")
            return None

    def _introspection(self, url: str) -> List[Dict]:
        resp = self._post(url, _INTROSPECTION)
        if not resp:
            return []
        text = getattr(resp, "text", "") or ""
        if getattr(resp, "status_code", 0) == 200 and (
            "__schema" in text or '"types"' in text or "queryType" in text
        ):
            return [{
                "type": "GraphQL Introspection Enabled",
                "severity": "medium",
                "url": url,
                "parameter": "query",
                "payload": "__schema",
                "evidence": text[:200],
                "description": "Full schema introspection allowed in production",
                "remediation": "Disable introspection outside dev; use persisted queries",
            }]
        return []

    def _batch(self, url: str) -> List[Dict]:
        batch = [{"query": "{ __typename }"} for _ in range(50)]
        resp = self._post(url, batch)
        if not resp:
            return []
        text = getattr(resp, "text", "") or ""
        if resp.status_code == 200 and text.count("__typename") >= 10:
            return [{
                "type": "GraphQL Batching Allowed",
                "severity": "medium",
                "url": url,
                "parameter": "",
                "payload": "50x {__typename}",
                "evidence": f"Batch of 50 returned HTTP {resp.status_code}",
                "description": "Unbounded GraphQL batching enables DoS / brute force amplification",
                "remediation": "Limit batch size and rate-limit GraphQL operations",
            }]
        return []

    def _aliases(self, url: str) -> List[Dict]:
        aliases = " ".join(f"a{i}: __typename" for i in range(40))
        q = {"query": "{ " + aliases + " }"}
        resp = self._post(url, q)
        if not resp:
            return []
        text = getattr(resp, "text", "") or ""
        if resp.status_code == 200 and text.count("__typename") + text.count('"a0"') > 5:
            return [{
                "type": "GraphQL Alias Overload",
                "severity": "medium",
                "url": url,
                "parameter": "",
                "payload": "40 aliases",
                "evidence": f"HTTP {resp.status_code} accepted large alias query",
                "description": "Alias flooding may bypass field limits",
                "remediation": "Cap aliases per query and total nodes",
            }]
        return []

    def _circular(self, url: str) -> List[Dict]:
        nest = "__typename"
        for _ in range(25):
            nest = f"__typename {nest}"
        q = {"query": "{ " + nest + " }"}
        resp = self._post(url, q)
        if resp and getattr(resp, "status_code", 0) == 200:
            return [{
                "type": "GraphQL Depth Budget Weak",
                "severity": "low",
                "url": url,
                "parameter": "",
                "payload": "depth~25",
                "evidence": f"HTTP {resp.status_code} on deep query",
                "description": "Deep queries accepted; ensure depth/complexity limits",
                "remediation": "Enforce max depth and query complexity analysis",
            }]
        return []

    def _variables(self, url: str) -> List[Dict]:
        findings = []
        for body in _VAR_INJECT:
            resp = self._post(url, body)
            if not resp:
                continue
            text = getattr(resp, "text", "") or ""
            st = getattr(resp, "status_code", 0)
            # reflection / error leakage of raw variable
            raw = json.dumps(body.get("variables") or {})
            markers = ("SQL", "syntax", "mongo", "Exception", "stack", "<script>", "169.254")
            if st == 200 and any(m.lower() in text.lower() for m in markers):
                findings.append({
                    "type": "GraphQL Variables Injection Leak",
                    "severity": "high",
                    "url": url,
                    "parameter": "variables",
                    "payload": raw[:120],
                    "evidence": text[:200],
                    "description": "GraphQL variables appear to trigger backend errors or reflection",
                    "remediation": "Validate variable types server-side; never interpolate into SQL/shell",
                })
                break
            if st in (200, 400) and any(
                v in text for v in (body.get("variables") or {}).values() if isinstance(v, str)
            ):
                findings.append({
                    "type": "GraphQL Variables Reflection",
                    "severity": "medium",
                    "url": url,
                    "parameter": "variables",
                    "payload": raw[:120],
                    "evidence": "Variable value reflected in GraphQL response",
                    "description": "Unencoded variable reflection can enable XSS or SSRF chains",
                    "remediation": "Encode outputs; treat variables as untrusted",
                })
                break
        return findings

    def _field_suggestion(self, url: str) -> List[Dict]:
        q = {"query": "{ __typenamee }"}  # typo to trigger suggestions
        resp = self._post(url, q)
        if not resp:
            return []
        text = getattr(resp, "text", "") or ""
        if "Did you mean" in text or "did you mean" in text.lower() or "suggestions" in text.lower():
            return [{
                "type": "GraphQL Field Suggestion Leak",
                "severity": "low",
                "url": url,
                "parameter": "query",
                "payload": "__typenamee",
                "evidence": text[:200],
                "description": "Error messages suggest field names (schema leak)",
                "remediation": "Disable field suggestions in production error formatter",
            }]
        return []
