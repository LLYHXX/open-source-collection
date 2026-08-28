"""AI attack planner: order checks + budget after recon."""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_ORDER = [
    "security_misconfiguration",
    "cors_csp",
    "jwt_deep",
    "ssrf",
    "sql_injection",
    "xss",
    "idor",
    "graphql_deep",
    "api_security",
]


class AIAttackPlanner:
    def __init__(self, ai_manager, config: Dict):
        self.ai_manager = ai_manager
        self.config = config
        self.cfg = config.get("ai_planner", {})

    def is_enabled(self) -> bool:
        return bool(self.cfg.get("enabled", False))

    def plan(
        self,
        recon_data: Optional[Dict] = None,
        enabled_checks: Optional[List[str]] = None,
    ) -> Dict:
        checks = list(enabled_checks or [])
        budget_seconds = int(self.cfg.get("budget_seconds", 600))
        max_urls = int(self.cfg.get("max_urls", 50))
        threads = int(self.cfg.get("threads", 5))

        tech = []
        if recon_data:
            tech = recon_data.get("technologies") or recon_data.get("tech") or []
            if isinstance(tech, dict):
                tech = list(tech.keys())

        order = list(_DEFAULT_ORDER)
        # heuristic boosts
        tech_s = " ".join(str(t) for t in tech).lower()
        if "graphql" in tech_s:
            order = ["graphql_deep"] + [c for c in order if c != "graphql_deep"]
        if "jwt" in tech_s or "oauth" in tech_s:
            order = ["jwt_deep", "oauth_testing"] + [
                c for c in order if c not in ("jwt_deep", "oauth_testing")
            ]

        if self.ai_manager and self.cfg.get("use_ai", True):
            try:
                prompt = (
                    "You are a pentester planner. Given tech stack and available checks, "
                    "return JSON only: {\"order\": [check_names], \"max_urls\": int, \"threads\": int}. "
                    f"Tech: {tech}. Checks: {checks[:40]}. BudgetSeconds: {budget_seconds}."
                )
                raw = self.ai_manager.generate(prompt) or ""
                m = re.search(r"\{[\s\S]*\}", raw)
                if m:
                    data = json.loads(m.group(0))
                    if isinstance(data.get("order"), list) and data["order"]:
                        order = [str(x) for x in data["order"]]
                    max_urls = int(data.get("max_urls", max_urls))
                    threads = int(data.get("threads", threads))
            except Exception as e:
                logger.debug(f"AI planner fallback: {e}")

        # keep only known enabled checks when provided
        if checks:
            known = set(checks)
            ordered = [c for c in order if c in known]
            ordered.extend([c for c in checks if c not in ordered])
            order = ordered

        threads = max(1, min(50, threads))
        max_urls = max(1, min(1000, max_urls))
        return {
            "order": order,
            "max_urls": max_urls,
            "threads": threads,
            "budget_seconds": budget_seconds,
        }
