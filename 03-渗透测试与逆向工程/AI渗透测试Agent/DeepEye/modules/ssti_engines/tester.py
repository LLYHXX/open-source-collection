"""Engine-specific SSTI deep tester (Jinja, FreeMarker, SpEL, etc.)."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

# Each probe: (payload, expected_substring, engine_name)
_PROBES = [
    # Polyglot math
    ("{{7*7}}", "49", "Jinja/Twig/Handlebars"),
    ("${7*7}", "49", "JSP/EL/FreeMarker"),
    ("<%=7*7%>", "49", "ERB/ASP"),
    ("${{7*7}}", "49", "Jinja2 expression"),
    ("#{7*7}", "49", "Pebble/Thymeleaf"),
    # Jinja-specific config / class access
    ("{{config.__class__}}", "config", "Jinja"),
    ("{{''.__class__.__mro__[1].__subclasses__()}}", "class", "Jinja"),
    # FreeMarker
    ("<#assign x=7*7>${x}", "49", "FreeMarker"),
    ("${7*7}", "49", "FreeMarker/EL"),
    # SpEL (Spring)
    ("${T(java.lang.Math).random()}", "0.", "SpEL"),
    ("${T(java.lang.Runtime).getRuntime()}", "java.lang.Runtime", "SpEL"),
    # Velocity
    ("#set($x=7*7)$x", "49", "Velocity"),
    # Django
    ("{% debug %}", "<class", "Django"),
    # Mako
    ("${7*7}", "49", "Mako"),
]

# Some engines echo the literal string when NOT vulnerable; we look for
# the *result* of evaluation rather than the literal.
_LITERAL_ECHOES = {"{{7*7}}", "${7*7}", "<%=7*7%>", "${{7*7}}", "#{7*7}"}


class SSTIEnginesTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        if not qs:
            return []

        vulns: List[Dict] = []
        for key in list(qs.keys())[:4]:
            for payload, expected, engine in _PROBES:
                try:
                    qs2 = {k: list(v) for k, v in qs.items()}
                    qs2[key] = [payload]
                    test_url = urlunparse(
                        parsed._replace(query=urlencode(qs2, doseq=True))
                    )
                    resp = self.http_client.get(test_url)
                    if not resp:
                        continue

                    body = getattr(resp, "text", "") or ""
                    status = getattr(resp, "status_code", 0)

                    # Positive signal: expected evaluation result present
                    # AND literal payload NOT echoed (to reduce false positives)
                    has_expected = expected in body
                    literal_echo = payload in body

                    if has_expected and not literal_echo:
                        vulns.append(
                            {
                                "type": f"Server-Side Template Injection ({engine})",
                                "severity": "critical",
                                "url": url,
                                "parameter": key,
                                "payload": payload,
                                "evidence": f"HTTP {status} – evaluated result '{expected}' found in response body",
                                "description": f"A {engine} template expression was evaluated server-side, indicating SSTI. This can lead to remote code execution.",
                                "remediation": "Use sandboxed template engines, avoid passing user input into template context, and apply strict output encoding.",
                            }
                        )
                        return vulns

                    # Secondary signal: 7777777 (7*7*7*7*7*7) for deep evaluation
                    if "7777777" in body and not literal_echo:
                        vulns.append(
                            {
                                "type": f"Server-Side Template Injection ({engine} – deep eval)",
                                "severity": "critical",
                                "url": url,
                                "parameter": key,
                                "payload": payload,
                                "evidence": f"HTTP {status} – deep evaluated result '7777777' found in response body",
                                "description": f"A {engine} template expression was deeply evaluated server-side, indicating SSTI with nested expression support. This can lead to remote code execution.",
                                "remediation": "Use sandboxed template engines, avoid passing user input into template context, and apply strict output encoding.",
                            }
                        )
                        return vulns

                except Exception as e:
                    logger.debug(f"ssti_engines: {e}")
        return vulns
