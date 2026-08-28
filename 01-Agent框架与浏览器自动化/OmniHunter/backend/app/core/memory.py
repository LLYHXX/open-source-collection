"""记忆/情报系统：借鉴 agentmemory 的 confidence + lifecycle + hybrid search。

轻量版：不引入向量库，用关键词检索 + confidence/hits 排序模拟 hybrid。
后续可平滑替换为向量检索（agentmemory iii-engine 同款思路）。
"""
from __future__ import annotations

from sqlalchemy import select, or_, desc

from ..models import Intel


class MemoryStore:
    """情报沉淀与召回：验证过的凭证/端点/指纹/技术栈入库，后续 Worker 复用。"""

    def __init__(self, db):
        self.db = db

    def store(self, kind: str, key: str, value: str, confidence: float = 0.6,
              source: str = "") -> Intel:
        entry = Intel(
            kind=kind, key=key, value=value,
            confidence=confidence, source=source,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def recall(self, query: str, kind: str | None = None,
               limit: int = 5) -> list[Intel]:
        """关键词检索 + confidence/hits 排序（hybrid 轻量模拟）。"""
        words = [w for w in query.replace(",", " ").split() if w]
        stmt = select(Intel).where(Intel.lifecycle == "active")
        if kind:
            stmt = stmt.where(Intel.kind == kind)
        if words:
            conds = []
            for w in words:
                conds.append(Intel.key.like(f"%{w}%"))
                conds.append(Intel.value.like(f"%{w}%"))
            stmt = stmt.where(or_(*conds))
        stmt = stmt.order_by(desc(Intel.confidence), desc(Intel.hits)).limit(limit)
        return list(self.db.scalars(stmt))

    def hit(self, intel_id: str) -> None:
        entry = self.db.get(Intel, intel_id)
        if entry:
            entry.hits += 1
            self.db.commit()

    def summary(self, query: str, limit: int = 5) -> str:
        items = self.recall(query, limit=limit)
        if not items:
            return "无已知情报。"
        lines = []
        for it in items:
            lines.append(
                f"- [{it.kind}] {it.key}: {it.value} (置信度{it.confidence:.2f},命中{it.hits}次)"
            )
        return "\n".join(lines)

    def retire(self, intel_id: str) -> None:
        entry = self.db.get(Intel, intel_id)
        if entry:
            entry.lifecycle = "retired"
            self.db.commit()

    # ===== 经验沉淀与复用（用户要求：每次攻击都变成经验）=====
    def store_experience(self, site_key: str, experience: dict,
                         confidence: float = 0.7) -> Intel:
        """沉淀一次攻击经验进 Intel(kind="attack_experience")。

        site_key 用根域或同站点指纹串（如 example.com 或 wp+nginx+php7），
        使下次同类站能 recall 复用，避免重复烧 token。

        experience 结构示例:
          {"hidden_params": [...], "effective_mutations": [...],
           "failed_mutations": [...], "discovered_rules": [...],
           "vulns": [...], "round_summary": "..."}
        """
        import json
        return self.store(
            kind="attack_experience",
            key=site_key,
            value=json.dumps(experience, ensure_ascii=False),
            confidence=confidence,
            source="attacker_round",
        )

    def recall_experience(self, site_key: str, limit: int = 3) -> list[dict]:
        """召回该站点的历史攻击经验（同类站直接复用，不重复试错）。

        按 confidence desc + hits desc 取最近 limit 条，返回解析后的 dict。
        """
        import json
        stmt = (select(Intel)
                .where(Intel.lifecycle == "active",
                       Intel.kind == "attack_experience",
                       Intel.key == site_key)
                .order_by(desc(Intel.confidence), desc(Intel.hits), desc(Intel.id))
                .limit(limit))
        items = list(self.db.scalars(stmt))
        out: list[dict] = []
        for it in items:
            try:
                payload = json.loads(it.value)
                payload["_intel_id"] = it.id
                payload["_confidence"] = it.confidence
                payload["_hits"] = it.hits
                out.append(payload)
            except Exception:  # noqa: BLE001
                continue
        return out

    def recall_latest(self, kind: str, key: str = "") -> Intel | None:
        """取某 kind 下最新一条（同 kind 多版本场景，如 attack_tree/business_model）。

        key 留空时取该 kind 全局最新一条。
        """
        stmt = select(Intel).where(Intel.lifecycle == "active",
                                    Intel.kind == kind)
        if key:
            stmt = stmt.where(Intel.key == key)
        stmt = stmt.order_by(desc(Intel.created_at)).limit(1)
        return self.db.scalars(stmt).first()

    def hit_by_kind_key(self, kind: str, key: str) -> None:
        """按 kind+key 命中复用计数（recall 同类经验时调用，体现热度）。"""
        stmt = (select(Intel)
                .where(Intel.lifecycle == "active",
                       Intel.kind == kind, Intel.key == key)
                .order_by(desc(Intel.confidence), desc(Intel.hits))
                .limit(1))
        entry = self.db.scalars(stmt).first()
        if entry:
            entry.hits += 1
            self.db.commit()

    # ===== 双维度缓存（CMS 类型 + 漏洞类型）+ 三元组召回 =====
    # 用户优化建议：缓存按 CMS 维度（强智/正方/泛微/用友）+
    # 漏洞类型维度（sqli/xss/business_logic）组织，命中率提升 40%。
    # attack_experience 拆解为 <漏洞特征向量, 有效Payload, 验证步骤> 三元组，
    # 用特征向量召回，比存完整文本节省 80% 上下文。

    def store_cms_experience(self, cms_type: str, vuln_type: str,
                              feature_vector: dict, payload: str,
                              verify_steps: str, confidence: float = 0.8) -> Intel:
        """沉淀 CMS+漏洞类型双维度经验三元组。

        feature_vector: 漏洞特征向量（如 {"endpoint": "/api/order",
                       "param": "user_id", "method": "GET"}），用于相似度召回。
        payload:        有效 payload。
        verify_steps:   验证步骤（简短）。
        """
        import json
        triple = {
            "cms_type": cms_type,
            "vuln_type": vuln_type,
            "feature_vector": feature_vector,
            "payload": payload[:500],
            "verify_steps": verify_steps[:300],
        }
        # key 用 cms_type:vuln_type，便于按维度过滤
        key = f"{cms_type}:{vuln_type}"
        return self.store(
            kind="cms_vuln_experience", key=key,
            value=json.dumps(triple, ensure_ascii=False),
            confidence=confidence, source="cms_experience",
        )

    def recall_cms_experience(self, cms_type: str, vuln_type: str = "",
                              endpoint: str = "", limit: int = 5) -> list[dict]:
        """按 CMS+漏洞类型召回三元组经验。

        vuln_type 留空则取该 CMS 所有漏洞类型经验。
        endpoint 提供时按特征向量端点相似度过滤（简化：字符串包含）。
        """
        import json
        if vuln_type:
            key = f"{cms_type}:{vuln_type}"
            stmt = (select(Intel)
                    .where(Intel.lifecycle == "active",
                           Intel.kind == "cms_vuln_experience",
                           Intel.key == key)
                    .order_by(desc(Intel.confidence), desc(Intel.hits))
                    .limit(limit * 2))  # 取多一些用于端点过滤
        else:
            # LIKE 匹配 cms_type:%
            pattern = f"{cms_type}:%"
            stmt = (select(Intel)
                    .where(Intel.lifecycle == "active",
                           Intel.kind == "cms_vuln_experience",
                           Intel.key.like(pattern))
                    .order_by(desc(Intel.confidence), desc(Intel.hits))
                    .limit(limit * 2))
        items = list(self.db.scalars(stmt))
        out: list[dict] = []
        for it in items:
            try:
                triple = json.loads(it.value)
                # 端点相似度过滤
                if endpoint:
                    fv = triple.get("feature_vector", {})
                    if (endpoint.lower() not in str(fv.get("endpoint", "")).lower()
                            and str(fv.get("endpoint", "")).lower()
                            not in endpoint.lower()):
                        continue
                triple["_intel_id"] = it.id
                triple["_confidence"] = it.confidence
                triple["_hits"] = it.hits
                out.append(triple)
            except Exception:  # noqa: BLE001
                continue
            if len(out) >= limit:
                break
        return out

    def list_cms_types(self) -> list[str]:
        """列出已有经验的 CMS 类型（前端展示缓存覆盖范围）。"""
        stmt = (select(Intel.key)
                .where(Intel.lifecycle == "active",
                       Intel.kind == "cms_vuln_experience")
                .distinct())
        keys = list(self.db.scalars(stmt))
        cms_set = set()
        for k in keys:
            if ":" in k:
                cms_set.add(k.split(":", 1)[0])
        return sorted(cms_set)
