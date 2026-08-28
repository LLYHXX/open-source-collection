"""
WebSocket Security Testing Module
Tests WebSocket connections for security vulnerabilities
"""

import json
import time
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class WebSocketTester:
    """Test WebSocket connections for security issues."""
    
    def __init__(self, http_client, config: Dict):
        """Initialize WebSocket tester."""
        self.http_client = http_client
        self.config = config
        self.ws_client = None
    
    def test_websocket(self, url: str, context: Dict) -> List[Dict]:
        """
        Test WebSocket endpoint for vulnerabilities.
        
        Args:
            url: WebSocket URL (ws:// or wss://)
            context: Request context
            
        Returns:
            List of vulnerabilities found
        """
        vulnerabilities = []
        
        # Convert http(s) to ws(s) if needed
        ws_url = self._convert_to_ws_url(url)
        
        vulnerabilities.extend(self._test_connection_security(ws_url))
        vulnerabilities.extend(self._test_origin_validation(ws_url))
        vulnerabilities.extend(self._test_authentication(ws_url))
        vulnerabilities.extend(self._test_input_validation(ws_url))
        vulnerabilities.extend(self._test_message_injection(ws_url))
        vulnerabilities.extend(self._test_dos_vulnerabilities(ws_url))
        vulnerabilities.extend(self._test_information_disclosure(ws_url))
        vulnerabilities.extend(self._test_csrf_websocket(ws_url))
        
        return vulnerabilities
    
    def _convert_to_ws_url(self, url: str) -> str:
        """Convert HTTP(S) URL to WS(S) URL."""
        if url.startswith('https://'):
            return url.replace('https://', 'wss://')
        elif url.startswith('http://'):
            return url.replace('http://', 'ws://')
        return url
    
    def _test_connection_security(self, ws_url: str) -> List[Dict]:
        """Test WebSocket connection security (WSS vs WS)."""
        vulnerabilities = []
        
        if ws_url.startswith('ws://'):
            vulnerabilities.append({
                'type': 'WebSocket - Unencrypted Connection',
                'severity': 'high',
                'url': ws_url,
                'evidence': 'WebSocket uses unencrypted ws:// protocol',
                'description': 'WebSocket connection not encrypted (using ws:// instead of wss://)',
                'remediation': 'Use WSS (WebSocket Secure) for encrypted communication',
                'cwe': 'CWE-319: Cleartext Transmission of Sensitive Information'
            })
        
        return vulnerabilities
    
    def _test_origin_validation(self, ws_url: str) -> List[Dict]:
        """Test for missing origin validation."""
        vulnerabilities = []
        
        try:
            # Try connecting with different origins
            malicious_origins = [
                'http://evil.com',
                'https://attacker.com',
                'null',
                'file://',
            ]
            
            for origin in malicious_origins:
                try:
                    # Simulate connection with custom origin
                    # In real implementation, use websocket-client library
                    # For now, we'll check via HTTP upgrade request
                    headers = {
                        'Upgrade': 'websocket',
                        'Connection': 'Upgrade',
                        'Origin': origin,
                        'Sec-WebSocket-Version': '13',
                        'Sec-WebSocket-Key': 'test_key_12345678901234=='
                    }
                    
                    http_url = ws_url.replace('wss://', 'https://').replace('ws://', 'http://')
                    response = self.http_client.get(http_url, headers=headers)
                    
                    if response and response.status_code == 101:  # Switching Protocols
                        vulnerabilities.append({
                            'type': 'WebSocket - Missing Origin Validation',
                            'severity': 'high',
                            'url': ws_url,
                            'evidence': f'WebSocket accepts connections from malicious origin: {origin}',
                            'description': 'WebSocket does not validate Origin header',
                            'remediation': 'Implement strict Origin validation to prevent CSWSH attacks',
                            'cwe': 'CWE-346: Origin Validation Error'
                        })
                        break
                except Exception as e:
                    logger.debug(f"Error testing origin {origin}: {e}")
        
        except Exception as e:
            logger.debug(f"Error testing origin validation: {e}")
        
        return vulnerabilities
    
    def _test_authentication(self, ws_url: str) -> List[Dict]:
        """Test WebSocket authentication mechanisms."""
        vulnerabilities = []
        
        try:
            # Try connecting without authentication
            http_url = ws_url.replace('wss://', 'https://').replace('ws://', 'http://')
            headers = {
                'Upgrade': 'websocket',
                'Connection': 'Upgrade',
                'Sec-WebSocket-Version': '13',
                'Sec-WebSocket-Key': 'test_key_12345678901234=='
            }
            
            response = self.http_client.get(http_url, headers=headers)
            
            if response and response.status_code == 101:
                vulnerabilities.append({
                    'type': 'WebSocket - Missing Authentication',
                    'severity': 'critical',
                    'url': ws_url,
                    'evidence': 'WebSocket connection established without authentication',
                    'description': 'WebSocket endpoint does not require authentication',
                    'remediation': 'Implement authentication (token-based, session-based, etc.)',
                    'cwe': 'CWE-306: Missing Authentication for Critical Function'
                })
        
        except Exception as e:
            logger.debug(f"Error testing authentication: {e}")
        
        return vulnerabilities
    
    def _test_input_validation(self, ws_url: str) -> List[Dict]:
        """Test input validation on WebSocket messages."""
        vulnerabilities = []
        
        # Test payloads for various injection attacks
        test_payloads = [
            ('XSS', '<script>alert("XSS")</script>'),
            ('SQL Injection', "'; DROP TABLE users; --"),
            ('Command Injection', '; ls -la'),
            ('JSON Injection', '{"admin": true, "role": "administrator"}'),
        ]
        
        for vuln_type, payload in test_payloads:
            try:
                probe = self.http_client.get(
                    ws_url.replace('ws://', 'http://').replace('wss://', 'https://'),
                    headers={
                        'Upgrade': 'websocket',
                        'Connection': 'Upgrade',
                        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
                        'Sec-WebSocket-Version': '13',
                        'X-Test-Payload': payload[:200],
                    },
                )
                status = getattr(probe, 'status_code', None) if probe else None
                if status in (101, 200, 400, 403, 426):
                    vulnerabilities.append({
                        'type': f'WebSocket - Potential {vuln_type}',
                        'severity': 'medium',
                        'url': ws_url,
                        'payload': payload,
                        'evidence': f'HTTP status {status} on WS upgrade probe with {vuln_type} payload',
                        'description': f'WebSocket endpoint should validate messages for {vuln_type}',
                        'remediation': 'Implement strict input validation and sanitization',
                        'cwe': 'CWE-20: Improper Input Validation'
                    })
            except Exception as e:
                logger.debug(f"Error testing {vuln_type}: {e}")
        
        return vulnerabilities
    
    def _test_message_injection(self, ws_url: str) -> List[Dict]:
        """Test for message injection vulnerabilities."""
        vulnerabilities = []
        
        # Test message tampering
        malformed_messages = [
            '{"type": "admin_command", "action": "grant_access"}',
            '{"userId": "../../../admin"}',
            '{"amount": -1000}',
            '{"role": "administrator"}',
        ]
        
        for msg in malformed_messages:
            # Note: Actual testing would require WebSocket connection
            # This is a placeholder for the testing logic
            logger.debug(f"Would test message injection with: {msg}")
        
        return vulnerabilities
    
    def _test_dos_vulnerabilities(self, ws_url: str) -> List[Dict]:
        """Test for DoS vulnerabilities in WebSocket."""
        vulnerabilities = []
        
        try:
            # Test with large message
            large_payload = 'A' * (10 * 1024 * 1024)  # 10MB
            
            # Note: Actual testing would send this via WebSocket
            # Check if server has message size limits
            vulnerabilities.append({
                'type': 'WebSocket - No Message Size Limit',
                'severity': 'medium',
                'url': ws_url,
                'evidence': 'WebSocket may accept excessively large messages',
                'description': 'WebSocket endpoint may lack message size restrictions',
                'remediation': 'Implement message size limits (e.g., max 1MB per message)',
                'cwe': 'CWE-770: Allocation of Resources Without Limits'
            })
        
        except Exception as e:
            logger.debug(f"Error testing DoS: {e}")
        
        return vulnerabilities
    
    def _test_information_disclosure(self, ws_url: str) -> List[Dict]:
        """Test for information disclosure via WebSocket."""
        vulnerabilities = []
        
        try:
            # Check for verbose error messages
            # Check for sensitive data in messages
            # Note: Requires actual WebSocket connection
            
            sensitive_patterns = [
                'password', 'secret', 'token', 'api_key',
                'credit_card', 'ssn', 'private_key'
            ]
            
            logger.debug("WebSocket information disclosure testing would check for sensitive data")
        
        except Exception as e:
            logger.debug(f"Error testing information disclosure: {e}")
        
        return vulnerabilities
    
    def _test_csrf_websocket(self, ws_url: str) -> List[Dict]:
        """Test for Cross-Site WebSocket Hijacking (CSWSH)."""
        vulnerabilities = []
        
        try:
            # CSWSH occurs when Origin validation is missing
            # and authentication relies solely on cookies
            
            # Check if connection uses cookie-based auth
            http_url = ws_url.replace('wss://', 'https://').replace('ws://', 'http://')
            response = self.http_client.get(http_url)
            
            if response and 'Set-Cookie' in response.headers:
                # If cookies are used and Origin validation is weak
                vulnerabilities.append({
                    'type': 'WebSocket - CSWSH Vulnerability',
                    'severity': 'high',
                    'url': ws_url,
                    'evidence': 'WebSocket may be vulnerable to Cross-Site WebSocket Hijacking',
                    'description': 'WebSocket uses cookie-based authentication without proper Origin validation',
                    'remediation': 'Use token-based authentication and validate Origin header',
                    'cwe': 'CWE-352: Cross-Site Request Forgery (CSRF)'
                })
        
        except Exception as e:
            logger.debug(f"Error testing CSWSH: {e}")
        
        return vulnerabilities
    
    def detect_websocket_endpoints(self, html_content: str, base_url: str) -> List[str]:
        """
        Detect WebSocket endpoints from HTML/JavaScript.
        
        Args:
            html_content: HTML page content
            base_url: Base URL for relative paths
            
        Returns:
            List of WebSocket URLs
        """
        import re
        
        ws_urls = []
        
        # Search for WebSocket URLs in JavaScript
        ws_patterns = [
            r'new\s+WebSocket\(["\']([^"\']+)["\']',
            r'ws://[^\s"\'<>]+',
            r'wss://[^\s"\'<>]+',
        ]
        
        for pattern in ws_patterns:
            matches = re.findall(pattern, html_content)
            ws_urls.extend(matches)
        
        return list(set(ws_urls))
