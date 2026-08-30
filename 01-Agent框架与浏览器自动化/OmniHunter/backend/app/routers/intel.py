"""情报/记忆库路由：列表（多维筛选）/ 新增 / 编辑 / 退役删除 / 导入导出 / 统计。

设计（工具为主 · 确定性操作 · 不依赖 LLM）：
- 查询：kind / lifecycle / confidence 区间 / 关键词 / 来源 / 分页
- 变更：全部走 POST（新增）/ PUT（编辑）/ DELETE（退役），严格校验 confidence∈[0,1]
- 导入导出：JSON 数组（[{kind,key,value,...}]），兼容 `intel export/import` 场景
- 统计：kind 分布 + lifecycle 分布 + 近 7 日增量 + Top hits 排行（纯 SQL 聚合，不依赖画图库）
"""
from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, and_, desc, or_, String
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import Intel
from ..schemas import IntelIn, IntelOut, StandardResponse

router = APIRouter(prefix="/intel", tags=["intel"], dependencies=[Depends(verify_token)])


def _intel_dict(it: Intel) -> dict:
    """ORM -> dict：把 datetime 字段序列化为 ISO 字符串，与 IntelOut schema 对齐。

    FR-A4: 若 value 匹配常见凭证 pattern，则附加 masked=true（前端决定是否折叠显示）。
    tags 字段：ORM JSON 列若为 None 回退到空 list。
    """
    def _fmt(v):
        if isinstance(v, datetime):
            return v.isoformat(sep=" ", timespec="seconds")
        return v
    value = it.value or ""
    masked = bool(re.search(
        r"(password|passwd|pwd|apikey|api[_\-]?key|api[_\-]?token|secret|authorization)\s*[:=]",
        value, re.IGNORECASE,
    ))
    tags = it.tags if isinstance(it.tags, list) else []
    return {
        "id": it.id,
        "kind": it.kind,
        "key": it.key,
        "value": value,
        "confidence": it.confidence,
        "hits": it.hits,
        "lifecycle": it.lifecycle,
        "source": it.source or "",
        "tags": tags,
        "masked": masked,
        "created_at": _fmt(it.created_at),
        "updated_at": _fmt(it.updated_at),
    }


# ========================== 列表与查询 ==========================

@router.get("", response_model=StandardResponse)
def list_intel(
    kind: str | None = None,
    lifecycle: str | None = None,
    conf_min: float = 0.0,
    conf_max: float = 1.0,
    q: str = "",
    source: str = "",
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    """多维筛选分页列表。返回 {items, total, kind_options}。"""
    if conf_min < 0: conf_min = 0
    if conf_max > 1: conf_max = 1
    if page < 1: page = 1
    if page_size < 1 or page_size > 500: page_size = 50

    stmt = select(Intel).where(
        Intel.confidence >= conf_min,
        Intel.confidence <= conf_max,
    )
    if kind:
        stmt = stmt.where(Intel.kind == kind)
    if lifecycle:
        stmt = stmt.where(Intel.lifecycle == lifecycle)
    if source:
        stmt = stmt.where(Intel.source == source)
    if q:
        kw = f"%{q}%"
        stmt = stmt.where(or_(
            Intel.key.like(kw),
            Intel.value.like(kw),
            Intel.source.like(kw),
        ))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    stmt = stmt.order_by(desc(Intel.updated_at)).offset((page - 1) * page_size).limit(page_size)
    items = [_intel_dict(i) for i in db.scalars(stmt)]

    # kind 候选（所有已出现的 kind 全量，供前端下拉）
    kinds_stmt = select(Intel.kind).distinct().order_by(Intel.kind)
    kind_options = [k for k in db.scalars(kinds_stmt) if k]

    return StandardResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "kind_options": kind_options,
    })


# ========================== 单条 CRUD ==========================

@router.post("", response_model=StandardResponse)
def create_intel(body: IntelIn, db: Session = Depends(get_db)):
    """新增一条情报。"""
    if not (0.0 <= body.confidence <= 1.0):
        raise HTTPException(400, "confidence 必须在 0~1 之间")
    if not body.kind:
        raise HTTPException(400, "kind 必填")
    it = Intel(
        kind=body.kind.strip()[:100],
        key=body.key.strip()[:500],
        value=body.value,
        confidence=body.confidence,
        source=body.source.strip()[:200],
        lifecycle=body.lifecycle or "active",
        tags=list(body.tags or []),
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    return StandardResponse(message="已添加", data=_intel_dict(it))


@router.get("/{intel_id}", response_model=StandardResponse)
def get_intel(intel_id: str, db: Session = Depends(get_db)):
    it = db.get(Intel, intel_id)
    if not it:
        raise HTTPException(404, "情报不存在")
    return StandardResponse(data=_intel_dict(it))


@router.put("/{intel_id}", response_model=StandardResponse)
def update_intel(intel_id: str, body: IntelIn, db: Session = Depends(get_db)):
    it = db.get(Intel, intel_id)
    if not it:
        raise HTTPException(404, "情报不存在")
    if not (0.0 <= body.confidence <= 1.0):
        raise HTTPException(400, "confidence 必须在 0~1 之间")
    if body.kind: it.kind = body.kind.strip()[:100]
    it.key = body.key.strip()[:500]
    it.value = body.value
    it.confidence = body.confidence
    it.source = body.source.strip()[:200]
    if body.lifecycle in ("active", "stale", "retired"):
        it.lifecycle = body.lifecycle
    if isinstance(body.tags, list):
        it.tags = [str(t) for t in body.tags[:200]]
    it.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(it)
    return StandardResponse(message="已更新", data=_intel_dict(it))


@router.delete("/{intel_id}", response_model=StandardResponse)
def retire_intel(intel_id: str, hard: bool = False, db: Session = Depends(get_db)):
    it = db.get(Intel, intel_id)
    if not it:
        raise HTTPException(404, "情报不存在")
    if hard:
        db.delete(it)
        db.commit()
        return StandardResponse(message="已物理删除")
    it.lifecycle = "retired"
    it.updated_at = datetime.utcnow()
    db.commit()
    return StandardResponse(message="已退役")


# ========================== 导入 / 导出 ==========================

_INTEL_KEYS = ("id", "kind", "key", "value", "confidence", "hits",
               "lifecycle", "source", "tags", "created_at", "updated_at")


@router.get("/export/json")
def export_json(kind: str | None = None, lifecycle: str = "active",
                conf_min: float = 0.0, conf_max: float = 1.0,
                q: str = "", source: str = "", db: Session = Depends(get_db)):
    """导出 JSON（查询条件与 list 接口一致）。"""
    stmt = select(Intel).where(
        Intel.confidence >= conf_min, Intel.confidence <= conf_max)
    if kind: stmt = stmt.where(Intel.kind == kind)
    if lifecycle: stmt = stmt.where(Intel.lifecycle == lifecycle)
    if source: stmt = stmt.where(Intel.source == source)
    if q:
        kw = f"%{q}%"
        stmt = stmt.where(or_(Intel.key.like(kw), Intel.value.like(kw), Intel.source.like(kw)))
    stmt = stmt.order_by(desc(Intel.updated_at))
    items = [_intel_dict(i) for i in db.scalars(stmt)]
    buf = io.BytesIO(json.dumps(items, ensure_ascii=False, indent=2).encode("utf-8"))
    return StreamingResponse(
        buf, media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=intel_export.json"},
    )


@router.get("/export/csv")
def export_csv(kind: str | None = None, lifecycle: str = "active",
               conf_min: float = 0.0, conf_max: float = 1.0,
               q: str = "", source: str = "", db: Session = Depends(get_db)):
    """导出 CSV。"""
    stmt = select(Intel).where(
        Intel.confidence >= conf_min, Intel.confidence <= conf_max)
    if kind: stmt = stmt.where(Intel.kind == kind)
    if lifecycle: stmt = stmt.where(Intel.lifecycle == lifecycle)
    if source: stmt = stmt.where(Intel.source == source)
    if q:
        kw = f"%{q}%"
        stmt = stmt.where(or_(Intel.key.like(kw), Intel.value.like(kw), Intel.source.like(kw)))
    stmt = stmt.order_by(desc(Intel.updated_at))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=_INTEL_KEYS, extrasaction="ignore")
    w.writeheader()
    for it in db.scalars(stmt):
        w.writerow(_intel_dict(it))
    data = io.BytesIO(buf.getvalue().encode("utf-8-sig"))  # BOM 以便 Excel 识别中文
    return StreamingResponse(
        data, media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=intel_export.csv"},
    )


@router.post("/import", response_model=StandardResponse)
async def import_intel(file: UploadFile = File(...),
                       mode: str = Form("merge"),  # merge / replace_kind / replace_all
                       db: Session = Depends(get_db)):
    """批量导入（JSON 或 CSV）。"""
    name = (file.filename or "").lower()
    raw = await file.read()
    rows: list[dict] = []
    if name.endswith(".json"):
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            raise HTTPException(400, f"JSON 解析失败: {e}")
        if not isinstance(payload, list):
            raise HTTPException(400, "导入文件必须是 JSON 数组")
        rows = [r for r in payload if isinstance(r, dict)]
    elif name.endswith(".csv"):
        try:
            text = raw.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            for r in reader:
                rows.append({k: v for k, v in r.items()})
        except Exception as e:  # noqa: BLE001
            raise HTTPException(400, f"CSV 解析失败: {e}")
    else:
        raise HTTPException(400, "仅支持 .json / .csv")

    # 白名单清洗：只保留允许字段，confidence/hits 做格式兜底
    clean_rows: list[dict] = []
    for r in rows:
        try:
            c = float(r.get("confidence", 0.6))
        except Exception:  # noqa: BLE001
            c = 0.6
        c = max(0.0, min(1.0, c))
        try:
            h = int(r.get("hits", 0))
        except Exception:  # noqa: BLE001
            h = 0
        tags_raw = r.get("tags") or []
        if isinstance(tags_raw, str):
            try:
                tags_raw = json.loads(tags_raw)
            except Exception:  # noqa: BLE001
                tags_raw = []
        tags = [str(x)[:80] for x in (tags_raw if isinstance(tags_raw, list) else [])][:200]
        clean_rows.append({
            "id": (r.get("id") or "").strip()[:40] or None,
            "kind": (r.get("kind") or "").strip()[:100],
            "key": (r.get("key") or "").strip()[:500],
            "value": str(r.get("value", "") or ""),
            "confidence": c,
            "hits": max(0, h),
            "lifecycle": r.get("lifecycle") or "active",
            "source": (r.get("source") or "").strip()[:200],
            "tags": tags,
        })

    # 模式：replace_all 先清空，replace_kind 按 kind 清空
    removed = 0
    if mode == "replace_all":
        removed = db.query(Intel).delete()
        db.flush()
    elif mode == "replace_kind":
        kinds = {r["kind"] for r in clean_rows if r["kind"]}
        for k in kinds:
            removed += db.query(Intel).filter(Intel.kind == k).count()
            db.query(Intel).filter(Intel.kind == k).delete()
        db.flush()

    added, updated = 0, 0
    for r in clean_rows:
        if not r["kind"]:
            continue
        existing = None
        if r["id"]:
            existing = db.get(Intel, r["id"])
        if existing:
            existing.kind = r["kind"]
            existing.key = r["key"]
            existing.value = r["value"]
            existing.confidence = r["confidence"]
            existing.hits = r["hits"]
            existing.lifecycle = r["lifecycle"]
            existing.source = r["source"]
            existing.tags = r.get("tags") or []
            existing.updated_at = datetime.utcnow()
            updated += 1
        else:
            db.add(Intel(**{k: v for k, v in r.items() if v is not None}))
            added += 1
    db.commit()
    return StandardResponse(
        message=f"导入完成：新增 {added}，更新 {updated}，清理 {removed}",
        data={"added": added, "updated": updated, "removed": removed},
    )


# ========================== 统计 ==========================

@router.get("/stats/summary", response_model=StandardResponse)
def stats_summary(db: Session = Depends(get_db)):
    """记忆系统统计总览：按 kind / lifecycle / 近 7 日 / Top hits。"""
    total_stmt = select(func.count(Intel.id))
    total = db.scalar(total_stmt) or 0
    active = db.scalar(select(func.count(Intel.id)).where(Intel.lifecycle == "active")) or 0
    retired = db.scalar(select(func.count(Intel.id)).where(Intel.lifecycle == "retired")) or 0
    stale = db.scalar(select(func.count(Intel.id)).where(Intel.lifecycle == "stale")) or 0
    total_hits = db.scalar(select(func.coalesce(func.sum(Intel.hits), 0))) or 0

    # kind 分布
    kind_stmt = (select(Intel.kind, func.count(Intel.id))
                 .group_by(Intel.kind).order_by(desc(func.count(Intel.id))))
    by_kind = [{"kind": k, "count": c} for k, c in db.execute(kind_stmt).all() if k]

    # lifecycle 分布（固定顺序）
    by_lifecycle = [
        {"status": "active", "count": active},
        {"status": "stale", "count": stale},
        {"status": "retired", "count": retired},
    ]

    # 近 7 日增量（按天）
    today = datetime.utcnow().date()
    daily = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        next_d = d + timedelta(days=1)
        c = db.scalar(select(func.count(Intel.id)).where(
            Intel.created_at >= d, Intel.created_at < next_d)) or 0
        daily.append({"date": d.isoformat(), "count": c})

    # Top hits 排行（前 10）
    top_hits_stmt = (select(Intel)
                     .order_by(desc(Intel.hits), desc(Intel.confidence))
                     .limit(10))
    top_hits = [_intel_dict(i) for i in db.scalars(top_hits_stmt) if i.hits > 0]

    return StandardResponse(data={
        "total": total,
        "active": active,
        "retired": retired,
        "stale": stale,
        "total_hits": total_hits,
        "by_kind": by_kind,
        "by_lifecycle": by_lifecycle,
        "daily_7d": daily,
        "top_hits": top_hits,
    })
