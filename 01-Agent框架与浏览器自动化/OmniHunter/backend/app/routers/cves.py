"""CVE 库路由：列表 / 详情 / 手动刷新 / 搜资产 / 触发扫描 / 命中资产列表。"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..config import get_settings
from ..database import SessionLocal, get_db
from ..models import CveAssetHit, CveEntry, Task
from ..schemas import (
    CveAssetHitOut,
    CveEntryOut,
    CveRefreshIn,
    CveScanIn,
    CveSearchAssetIn,
    StandardResponse,
)

log = logging.getLogger("aififteen-hunter")

router = APIRouter(prefix="/cves", tags=["cves"],
                   dependencies=[Depends(verify_token)])


@router.get("", response_model=StandardResponse)
def list_cves(
    keyword: str = Query("", description="关键字（CVE-ID/title/description/product）"),
    severity: str = Query("", description="严重等级过滤：LOW/MEDIUM/HIGH/CRITICAL"),
    source: str = Query("", description="来源过滤：nvd/osv"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """CVE 库分页列表：支持关键字 + 严重等级 + 来源过滤。"""
    q = select(CveEntry)
    if keyword:
        kw = f"%{keyword}%"
        q = q.where(or_(
            CveEntry.cve_id.like(kw),
            CveEntry.title.like(kw),
            CveEntry.description.like(kw),
        ))
    if severity:
        q = q.where(CveEntry.cvss_severity == severity.upper())
    if source:
        q = q.where(CveEntry.source == source.lower())

    from sqlalchemy import func
    total = db.scalar(select(func.count()).select_from(
        q.with_only_columns(CveEntry.id).order_by(None).subquery()
    )) or 0

    rows = db.scalars(
        q.order_by(desc(CveEntry.published_at)).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return StandardResponse(
        message=f"共 {total} 条，当前第 {page} 页",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [CveEntryOut.model_validate(r).model_dump() for r in rows],
        },
    )


@router.get("/stats", response_model=StandardResponse)
def cve_stats(db: Session = Depends(get_db)):
    """CVE 库统计：总数、按严重等级分布、按来源分布、最近 7 天新增。"""
    from datetime import datetime, timedelta

    from sqlalchemy import func

    total = db.scalar(select(func.count(CveEntry.id))) or 0
    severity_rows = db.execute(
        select(CveEntry.cvss_severity, func.count())
        .group_by(CveEntry.cvss_severity)
    ).all()
    source_rows = db.execute(
        select(CveEntry.source, func.count()).group_by(CveEntry.source)
    ).all()
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent = db.scalar(
        select(func.count(CveEntry.id)).where(CveEntry.created_at >= seven_days_ago)
    ) or 0

    pending_hits = db.scalar(
        select(func.count(CveAssetHit.id)).where(CveAssetHit.scan_status == "pending")
    ) or 0
    return StandardResponse(data={
        "total": total,
        "recent_7d": recent,
        "by_severity": {k or "UNKNOWN": v for k, v in severity_rows},
        "by_source": {k: v for k, v in source_rows},
        "pending_asset_hits": pending_hits,
    })


@router.get("/{cve_id}", response_model=StandardResponse)
def get_cve(cve_id: str, db: Session = Depends(get_db)):
    """CVE 详情：含 affected / references。"""
    cve = db.scalar(select(CveEntry).where(CveEntry.cve_id == cve_id))
    if not cve:
        raise HTTPException(404, f"CVE 不存在: {cve_id}")
    return StandardResponse(data=CveEntryOut.model_validate(cve).model_dump())


@router.post("/refresh", response_model=StandardResponse)
async def refresh_cves(payload: CveRefreshIn, db: Session = Depends(get_db)):
    """手动刷新 CVE 库：拉取最近 N 天，source=nvd/osv/all。"""
    settings = get_settings()
    from ..tools.cve_fetcher import fetch_and_update_cves
    result = await fetch_and_update_cves(
        settings, db, days=payload.days, source=payload.source,
    )
    msg = (f"CVE 库刷新完成：新增 {result.get('added', 0)}，"
           f"更新 {result.get('updated', 0)}")
    if result.get("errors"):
        msg += f"，错误 {len(result['errors'])} 条"
    return StandardResponse(message=msg, data=result)


@router.post("/search-assets", response_model=StandardResponse)
async def search_assets(payload: CveSearchAssetIn, db: Session = Depends(get_db)):
    """按 CVE 搜未修复资产：affected → 各平台查询语句 → 资产命中入库。"""
    cve = db.scalar(select(CveEntry).where(CveEntry.cve_id == payload.cve_id))
    if not cve:
        raise HTTPException(404, f"CVE 不存在: {payload.cve_id}")

    settings = get_settings()
    from ..tools.asset_platforms import search_by_cve

    cve_dict = {
        "cve_id": cve.cve_id,
        "affected": cve.affected or {},
        "cvss_score": cve.cvss_score,
        "cvss_severity": cve.cvss_severity,
    }
    # search_by_cve 是同步函数（httpx 同步客户端），放线程池
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: search_by_cve(
            cve_dict, settings,
            platforms=payload.platforms or None,
            max_results=payload.max_results,
        )
    )
    # 入库命中资产
    added = 0
    for it in result.get("items", []):
        hit = CveAssetHit(
            cve_id=cve.cve_id,
            url=it.get("url", ""),
            host=it.get("host", ""),
            port=int(it.get("port", 0) or 0),
            title=it.get("title", ""),
            platform=it.get("platform", ""),
            query=it.get("query", ""),
            scan_status="pending",
        )
        db.add(hit)
        added += 1
    db.commit()
    msg = (f"搜到 {len(result.get('items', []))} 个资产，入库 {added} 条"
           f"（{len(result.get('errors', {}))} 个平台失败）")
    return StandardResponse(message=msg, data=result)


@router.get("/asset-hits", response_model=StandardResponse)
def list_asset_hits(
    cve_id: str = Query("", description="按 CVE 过滤"),
    scan_status: str = Query("", description="按扫描状态过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """CVE 资产命中列表（待扫描 / 已扫描）。"""
    from sqlalchemy import func

    q = select(CveAssetHit)
    if cve_id:
        q = q.where(CveAssetHit.cve_id == cve_id)
    if scan_status:
        # 中文映射（前端可能传「待审核」等）
        status_map = {"待审核": "pending", "扫描中": "scanning",
                      "已完成": "done", "失败": "failed", "已跳过": "skipped"}
        s = status_map.get(scan_status, scan_status)
        q = q.where(CveAssetHit.scan_status == s)

    total = db.scalar(select(func.count()).select_from(
        q.with_only_columns(CveAssetHit.id).order_by(None).subquery()
    )) or 0
    rows = db.scalars(
        q.order_by(desc(CveAssetHit.created_at))
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return StandardResponse(
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [CveAssetHitOut.model_validate(r).model_dump() for r in rows],
        }
    )


@router.post("/scan", response_model=StandardResponse)
async def scan_assets(payload: CveScanIn, db: Session = Depends(get_db)):
    """基于 CVE 命中资产触发挖掘流水线。

    pipeline: engine（自研引擎扫描）/ collab（单站协作）/ traffic（流量挖掘）
    """
    q = select(CveAssetHit).where(
        CveAssetHit.cve_id == payload.cve_id,
        CveAssetHit.scan_status == "pending",
    )
    if payload.hit_ids:
        q = q.where(CveAssetHit.id.in_(payload.hit_ids))
    hits = db.scalars(q).all()
    if not hits:
        raise HTTPException(400, f"无待扫描的命中资产: CVE={payload.cve_id}")

    # 创建任务
    task = Task(
        name=f"CVE 扫描 {payload.cve_id} ({len(hits)} 个资产)",
        mode="engine" if payload.pipeline == "engine" else "EduSRC",
        source="cve",
        manual_targets="\n".join(h.url for h in hits if h.url),
        status="running",
    )
    db.add(task)
    for h in hits:
        h.task_id = task.id
        h.scan_status = "scanning"
    db.commit()

    # 后台执行流水线
    pipeline = payload.pipeline
    task_id = task.id
    hit_ids = [h.id for h in hits]

    async def _bg():
        db2 = SessionLocal()
        try:
            await _run_cve_scan_pipeline(db2, task_id, hit_ids, pipeline)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    return StandardResponse(
        message=f"已对 CVE {payload.cve_id} 启动 {pipeline} 扫描（任务 {task_id}，{len(hits)} 个资产）",
        data={"task_id": task_id, "hit_count": len(hits)},
    )


async def _run_cve_scan_pipeline(db: Session, task_id: str,
                                  hit_ids: list[str], pipeline: str) -> None:
    """后台执行 CVE 扫描：对每个命中资产跑对应流水线，更新状态。"""
    from ..core.orchestrator import Orchestrator

    orch = Orchestrator(db)
    task = db.get(Task, task_id)
    if not task:
        return

    success_count = 0
    fail_count = 0
    for hit_id in hit_ids:
        hit = db.get(CveAssetHit, hit_id)
        if not hit or not hit.url:
            continue
        try:
            if pipeline == "engine":
                await orch.run_engine_pipeline(task, hit.url)
            elif pipeline == "collab":
                await orch.run_collab_pipeline(task, hit.url)
            elif pipeline == "traffic":
                await orch.run_traffic_pipeline(task, hit.url)
            else:
                # 默认引擎
                await orch.run_engine_pipeline(task, hit.url)
            hit.scan_status = "done"
            success_count += 1
        except Exception as e:  # noqa: BLE001
            hit.scan_status = "failed"
            fail_count += 1
            log.warning("CVE 扫描失败 %s: %s", hit.url, e)
        db.commit()

    task.status = "review"
    db.commit()
    log.info("CVE 扫描完成: 任务 %s, 成功 %d, 失败 %d",
             task_id, success_count, fail_count)


@router.delete("/asset-hits/{hit_id}", response_model=StandardResponse)
def delete_asset_hit(hit_id: str, db: Session = Depends(get_db)):
    """删除单个命中资产记录。"""
    hit = db.get(CveAssetHit, hit_id)
    if not hit:
        raise HTTPException(404, "命中资产不存在")
    if hit.scan_status == "scanning":
        raise HTTPException(400, "正在扫描中，无法删除")
    db.delete(hit)
    db.commit()
    return StandardResponse(message="已删除")


@router.delete("/{cve_id}", response_model=StandardResponse)
def delete_cve(cve_id: str, db: Session = Depends(get_db)):
    """删除 CVE 条目（同时级联删除其命中资产）。"""
    cve = db.scalar(select(CveEntry).where(CveEntry.cve_id == cve_id))
    if not cve:
        raise HTTPException(404, f"CVE 不存在: {cve_id}")
    # 先删除关联命中
    hits = db.scalars(select(CveAssetHit).where(CveAssetHit.cve_id == cve_id)).all()
    for h in hits:
        db.delete(h)
    db.delete(cve)
    db.commit()
    return StandardResponse(message=f"已删除 CVE {cve_id}（含 {len(hits)} 条命中资产）")
