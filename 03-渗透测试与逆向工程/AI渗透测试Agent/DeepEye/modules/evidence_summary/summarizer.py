"""Per-finding evidence LLM summary for bounty quality."""
from __future__ import annotations

from typing import Dict, List

from utils.logger import get_logger

logger = get_logger(__name__)


class EvidenceSummarizer:
    def __init__(self, ai_manager, config: Dict):
        self.ai_manager = ai_manager
        self.config = config
        self.cfg = config.get("evidence_summary", {})

    def is_enabled(self) -> bool:
        return bool(self.cfg.get("enabled", False)) and self.ai_manager is not None

    def enrich(self, vulns: List[Dict]) -> List[Dict]:
        if not self.is_enabled():
            return vulns
        min_sev = str(self.cfg.get("min_severity", "high")).lower()
        rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        min_r = rank.get(min_sev, 3)
        limit = int(self.cfg.get("max_findings", 15))
        n = 0
        for v in vulns:
            if n >= limit:
                break
            if rank.get(str(v.get("severity", "info")).lower(), 0) < min_r:
                continue
            try:
                prompt = (
                    "Write 3 short bullets for a bug bounty report: "
                    "(1) why this is real, (2) impact, (3) how to exploit. "
                    "Be concrete. Finding JSON:\n"
                    f"type={v.get('type')} severity={v.get('severity')} url={v.get('url')} "
                    f"param={v.get('parameter')} payload={str(v.get('payload',''))[:200]} "
                    f"evidence={str(v.get('evidence',''))[:400]}"
                )
                text = (self.ai_manager.generate(prompt) or "").strip()
                if text:
                    v["ai_evidence_summary"] = text[:2000]
                    n += 1
            except Exception as e:
                logger.debug(f"evidence summary failed: {e}")
        return vulns
