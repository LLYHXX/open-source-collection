"""Natural-language scope → ScopeManager-compatible dict."""
from __future__ import annotations

import re
from typing import Dict, List


def parse_nl_scope(text: str) -> Dict:
    """
    Parse phrases like:
      only /api/* and /v1/*
      no /logout, exclude /admin
      host target.com and *.example.com
      ports 80,443,8080
    """
    text = (text or "").strip()
    result: Dict = {
        "enabled": True,
        "allowed_hosts": [],
        "excluded_paths": [],
        "allowed_ports": [],
        "path_allow": [],
    }
    if not text:
        result["enabled"] = False
        return result

    lower = text.lower()

    for m in re.finditer(
        r"(?:host|hosts?|domain)\s+([a-z0-9.*_-]+)", lower, re.I
    ):
        result["allowed_hosts"].append(m.group(1))
    for m in re.finditer(r"\*\.[a-z0-9.-]+", lower):
        result["allowed_hosts"].append(m.group(0))

    ports = re.search(r"ports?\s+([\d,\s]+)", lower)
    if ports:
        result["allowed_ports"] = [
            int(p.strip()) for p in ports.group(1).split(",") if p.strip().isdigit()
        ]

    for m in re.finditer(
        r"(?:only|allow|include)\s+((?:/[\w*/.{}\[\]-]+\s*(?:,\s*)?)+)",
        text,
        re.I,
    ):
        for path in re.findall(r"/[\w*/.{}\[\]-]+", m.group(1)):
            result["path_allow"].append(path)

    for m in re.finditer(
        r"(?:no|not|exclude|skip)\s+((?:/[\w*/.{}\[\]-]+\s*(?:,\s*)?)+)",
        text,
        re.I,
    ):
        for path in re.findall(r"/[\w*/.{}\[\]-]+", m.group(1)):
            # ScopeManager uses regex on path
            pat = path.replace(".", r"\.").replace("*", ".*")
            result["excluded_paths"].append(pat)

    if not any(
        [
            result["allowed_hosts"],
            result["excluded_paths"],
            result["allowed_ports"],
            result["path_allow"],
        ]
    ):
        result["enabled"] = False
    return result


def apply_nl_scope_to_config(config: Dict, text: str) -> Dict:
    parsed = parse_nl_scope(text)
    if not parsed.get("enabled"):
        return config
    scope = dict(config.get("scope") or {})
    scope["enabled"] = True
    if parsed["allowed_hosts"]:
        scope["allowed_hosts"] = list(
            dict.fromkeys((scope.get("allowed_hosts") or []) + parsed["allowed_hosts"])
        )
    if parsed["excluded_paths"]:
        scope["excluded_paths"] = list(
            dict.fromkeys((scope.get("excluded_paths") or []) + parsed["excluded_paths"])
        )
    if parsed["allowed_ports"]:
        scope["allowed_ports"] = list(
            dict.fromkeys((scope.get("allowed_ports") or []) + parsed["allowed_ports"])
        )
    if parsed["path_allow"]:
        scope["path_allow"] = list(
            dict.fromkeys((scope.get("path_allow") or []) + parsed["path_allow"])
        )
    config = dict(config)
    config["scope"] = scope
    return config
