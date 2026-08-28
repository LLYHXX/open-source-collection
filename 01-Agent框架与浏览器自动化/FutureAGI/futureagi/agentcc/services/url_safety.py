import ipaddress
import socket
from urllib.parse import urlparse

import requests as http_requests

BLOCKED_PORTS = {6379, 5432, 3306, 27017, 9200, 11211, 2379}
WEBHOOK_PRIVATE_URL_ERROR = "Webhook URL cannot point to internal or private addresses"


def _raise_if_unsafe_url(
    url: str, message: str, exception_cls: type[Exception]
) -> None:
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port
    scheme = parsed.scheme.lower()

    if not hostname or scheme not in ("http", "https"):
        raise exception_cls(message)

    if port and port in BLOCKED_PORTS:
        raise exception_cls(message)

    try:
        resolved = socket.getaddrinfo(
            hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM
        )
    except socket.gaierror:
        raise exception_cls(message)

    for _, _, _, _, sockaddr in resolved:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise exception_cls(message)


def ensure_public_http_url(url: str, error_message: str) -> None:
    _raise_if_unsafe_url(url, error_message, ValueError)


def build_ssrf_safe_session(connect_error_message: str) -> http_requests.Session:
    class _SSRFSafeAdapter(http_requests.adapters.HTTPAdapter):
        def send(self, request, **kwargs):
            _raise_if_unsafe_url(request.url, connect_error_message, ConnectionError)
            return super().send(request, **kwargs)

    session = http_requests.Session()
    adapter = _SSRFSafeAdapter()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
