"""Payload encoding helpers for WAF-bypass variants."""
from __future__ import annotations

import urllib.parse
from typing import Dict, List


_TECHNIQUES = {
    "url_encoding",
    "double_url_encoding",
    "case_manipulation",
    "html_entity",
    "unicode_escape",
    "comment_insert",
    "null_byte",
    "space_to_plus",
    "tab_replace",
}


def obfuscate_payload(payload: str, techniques: List[str] = None) -> List[str]:
    """Return variants of payload using named techniques."""
    if techniques is None:
        techniques = ["url_encoding", "case_manipulation"]
    unknown = [t for t in techniques if t not in _TECHNIQUES]
    if unknown:
        raise KeyError(
            f"Unknown techniques {unknown}; known={sorted(_TECHNIQUES)}"
        )
    out = [payload]
    for tech in techniques:
        out.extend(_apply(payload, tech))
    # unique preserve order
    return list(dict.fromkeys(out))


def _apply(payload: str, tech: str) -> List[str]:
    if tech == "url_encoding":
        return [urllib.parse.quote(payload, safe="")]
    if tech == "double_url_encoding":
        return [urllib.parse.quote(urllib.parse.quote(payload, safe=""), safe="")]
    if tech == "case_manipulation":
        return [payload.swapcase(), payload.upper(), payload.lower()]
    if tech == "html_entity":
        return ["".join(f"&#{ord(c)};" for c in payload[:40])]
    if tech == "unicode_escape":
        return [payload.encode("unicode_escape").decode("ascii")]
    if tech == "comment_insert":
        if " " in payload:
            return [payload.replace(" ", "/**/", 1)]
        return [payload[:1] + "/**/" + payload[1:]] if len(payload) > 1 else [payload]
    if tech == "null_byte":
        return [payload + "%00", "%00" + payload]
    if tech == "space_to_plus":
        return [payload.replace(" ", "+")]
    if tech == "tab_replace":
        return [payload.replace(" ", "\t")]
    return []


def known_techniques() -> List[str]:
    return sorted(_TECHNIQUES)
