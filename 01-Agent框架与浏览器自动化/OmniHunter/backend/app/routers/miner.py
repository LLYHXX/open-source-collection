"""Autonomous Miner 路由。

严格边界：
  * GET  /config        → 当前 MinerConfig（Setting 表前缀 miner.）
  * PUT  /config        → 校验 scope 非空才能 enabled → 写入 Setting → 刷新 APScheduler cron
  * POST /trigger-once  → 后台跑一次 run_miner_once（不阻塞 HTTP）
  * GET  /runs          → 最近 N 条 MinerRun 审计
  * GET  /candidates    → MinerCandidate 分页 + 按 status 过滤（默认 pending）
  * POST /candidates/approve  → 批量批准 → 写 Intel + 改 status=approved
  * POST /candidates/reject   → 批量改 status=rejected
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..core.miner import (
    MINER_AUTO_APPROVE_ALL,
    MINER_AUTO_APPROVE_OFF,
    MINER_AUTO_APPROVE_REVERIFY,
    MinerConfig,
    load_miner_config,
    run_miner_once,
    save_miner_config,
    trigger_miner_cron_refresh,
)
from ..database import get_db
from ..models import Intel, MinerCandidate, MinerRun, Setting
from ..schemas import StandardResponse

router = APIRouter(prefix="/miner", tags=["miner"],
                   dependencies=[Depends(verify_token)])

log = logging.getLogger("aififteen-hunter.miner.router")


class MinerConfigIn(BaseModel):
    enabled: bool = False
    scope_asset_ids: list[str] = Field(default_factory=list)
    daily_budget_max_jobs: int = 20
    max_runtime_min: int = 120
    auto_approve: str = MINER_AUTO_APPROVE_REVERIFY
    cron_expr: str = "0 2 * * *"


class MinerCandidateBatch(BaseModel):
    ids: list[str] = Field(default_factory=list)


def _cfg_out(cfg: MinerConfig) -> dict:
    return {
        "enabled": cfg.enabled,
        "scope_asset_ids": list(cfg.scope_asset_ids or []),
        "daily_budget_max_jobs": int(cfg.daily_budget_max_jobs),
        "max_runtime_min": int(cfg.max_runtime_min),
        "auto_approve": cfg.auto_approve,
        "cron_expr": cfg.cron_expr,
    }


@router.get("/config", response_model=StandardResponse)
def get_config(db: Session = Depends(get_db)):
    cfg = load_miner_config(db)
    return StandardResponse(message="ok", data=_cfg_out(cfg))


@router.put("/config", response_model=StandardResponse)
def update_config(payload: MinerConfigIn, db: Session = Depends(get_db)):
    # 基本校验：budget/runtime 范围
    if payload.daily_budget_max_jobs < 1 or payload.daily_budget_max_jobs > 200:
        raise HTTPException(400, "daily_budget_max_jobs 必须为 1~200 整数")
    if payload.max_runtime_min < 5 or payload.max_runtime_min > 1440:
        raise HTTPException(400, "max_runtime_min 必须为 5~1440 整数")
    # 策略白名单
    if payload.auto_approve not in (
        MINER_AUTO_APPROVE_REVERIFY, MINER_AUTO_APPROVE_ALL, MINER_AUTO_APPROVE_OFF,
    ):
        raise HTTPException(400, f"auto_approve 非法值: {payload.auto_approve}")

    # scope 清洗：去重 + 去空
    scope_clean = list({str(s).strip() for s in (payload.scope_asset_ids or []) if str(s).strip()})
    if payload.enabled and not scope_clean:
        raise HTTPException(
            400,
            "scope_asset_ids 不能为空：启用 Miner 前必须先设置授权资产域（限域合规要求）",
        )

    cfg = MinerConfig(
        enabled=bool(payload.enabled),
        scope_asset_ids=scope_clean,
        daily_budget_max_jobs=int(payload.daily_budget_max_jobs),
        max_runtime_min=int(payload.max_runtime_min),
        auto_approve=payload.auto_approve,
        cron_expr=(payload.cron_expr or "0 2 * * *").strip() or "0 2 * * *",
    )
    save_miner_config(db, cfg)
    db.commit()

    # 动态覆盖到 settings 实例（让 apply_dynamic_overrides 感知）
    try:
        from ..config import apply_dynamic_overrides
        overrides: dict[str, str] = {}
        for s in db.scalars(select(Setting).where(Setting.key.like("miner.%"))):
            overrides[s.key] = s.value
        apply_dynamic_overrides(overrides)
    except Exception as e:  # noqa: BLE001
        log.warning("Miner 动态配置 apply 失败（不阻塞）: %s", e)

    # 刷新 APScheduler cron trigger
    try:
        trigger_miner_cron_refresh(cfg.cron_expr)
    except Exception as e:  # noqa: BLE001
        log.warning("Miner cron 刷新失败（可能 APScheduler 尚未启动）: %s", e)

    return StandardResponse(
        message="Miner 配置已保存；cron 刷新若需立即生效无需重启后端",
        data=_cfg_out(cfg),
    )


@router.post("/trigger-once", response_model=StandardResponse)
async def trigger_once():
    """立即触发一次 Miner 三 Loop；返回 running in background，结果查 GET /runs。"""
    async def _bg():
        try:
            await run_miner_once(trigger_from="manual")
        except Exception as e:  # noqa: BLE001
            log.error("Miner trigger-once 后台异常: %s", e)
    asyncio.create_task(_bg())
    return StandardResponse(message="Miner 单轮已在后台执行；可通过 GET /miner/runs 查看执行结果")


@router.get("/runs", response_model=StandardResponse)
def list_runs(limit: int = 30, db: Session = Depends(get_db)):
    limit = max(1, min(100, int(limit)))
    rows = db.scalars(
        select(MinerRun).order_by(MinerRun.trigger_at.desc()).limit(limit)
    ).all()
    data = []
    for r in rows:
        data.append({
            "id": r.id, "trigger_at": r.trigger_at.isoformat() if r.trigger_at else None,
            "trigger_from": r.trigger_from,
            "loop1_coverage_count": r.loop1_coverage_count,
            "loop2_reverify_count": r.loop2_reverify_count,
            "loop3_link_count": r.loop3_link_count,
            "budget_hit_limit": bool(r.budget_hit_limit),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "error_log": r.error_log or "",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return StandardResponse(message=f"共 {len(data)} 条", data=data)


@router.get("/candidates", response_model=StandardResponse)
def list_candidates(status: str = "pending", page: int = 1, page_size: int = 50,
                    db: Session = Depends(get_db)):
    page = max(1, int(page))
    page_size = max(1, min(500, int(page_size)))
    valid_status = {"pending", "approved", "rejected", "skipped"}
    if status not in valid_status:
        raise HTTPException(400, f"status 非法，允许值: {sorted(valid_status)}")
    total = int(db.scalar(
        select(func.count(MinerCandidate.id))
        .where(MinerCandidate.status == status)
    ) or 0)
    stmt = (
        select(MinerCandidate)
        .where(MinerCandidate.status == status)
        .order_by(MinerCandidate.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.scalars(stmt).all()

    def dump(c: MinerCandidate) -> dict:
        return {
            "id": c.id, "src_intel_id": c.src_intel_id,
            "extracted_kind": c.extracted_kind, "extracted_key": c.extracted_key,
            "status": c.status, "note": c.note or "",
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
    return StandardResponse(
        message=f"status={status} total={total}",
        data={"items": [dump(c) for c in items], "total": total, "page": page, "page_size": page_size},
    )


@router.post("/candidates/approve", response_model=StandardResponse)
def approve_candidates(payload: MinerCandidateBatch, db: Session = Depends(get_db)):
    ids = [str(s).strip() for s in (payload.ids or []) if str(s).strip()]
    if not ids:
        raise HTTPException(400, "ids 不能为空")
    cands = db.scalars(
        select(MinerCandidate).where(MinerCandidate.id.in_(ids))
    ).all()
    by_id = {c.id: c for c in cands}
    wrote_intel = 0
    processed = 0
    for cid in ids:
        cand = by_id.get(cid)
        if cand is None:
            continue
        if cand.status not in ("pending", "rejected"):
            # approved / skipped 不动
            continue
        # approved 写 Intel（幂等：同 key + kind + value 不重复写）
        kind = cand.extracted_kind or "unknown"
        key = cand.extracted_key or ""
        value = key
        existing = db.scalar(
            select(Intel.id)
            .where(Intel.kind == kind)
            .where(Intel.key == key)
            .limit(1)
        )
        if existing is None:
            intel = Intel(
                kind=kind, key=key, value=value, lifecycle="active",
                confidence=0.7, source="miner:candidate_approve",
                tags=["MINER_APPROVED", f"from_{cand.src_intel_id or 'src_unknown'}"],
            )
            db.add(intel)
            wrote_intel += 1
        cand.status = "approved"
        cand.note = (cand.note or "") + "; approved_at=" + datetime.utcnow().isoformat()
        processed += 1
    db.commit()
    return StandardResponse(
        message=f"已处理 {processed} 条，写入 Intel {wrote_intel} 条",
        data={"processed": processed, "wrote_intel": wrote_intel},
    )


@router.post("/candidates/reject", response_model=StandardResponse)
def reject_candidates(payload: MinerCandidateBatch, db: Session = Depends(get_db)):
    ids = [str(s).strip() for s in (payload.ids or []) if str(s).strip()]
    if not ids:
        raise HTTPException(400, "ids 不能为空")
    cands = db.scalars(
        select(MinerCandidate).where(MinerCandidate.id.in_(ids))
    ).all()
    by_id = {c.id: c for c in cands}
    processed = 0
    for cid in ids:
        cand = by_id.get(cid)
        if cand is None:
            continue
        if cand.status in ("approved", "skipped"):
            continue
        cand.status = "rejected"
        cand.note = (cand.note or "") + "; rejected_at=" + datetime.utcnow().isoformat()
        processed += 1
    db.commit()
    return StandardResponse(message=f"已拒绝 {processed} 条", data={"processed": processed})
