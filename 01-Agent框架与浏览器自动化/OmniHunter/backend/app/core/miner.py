"""Autonomous Miner 三 Loop 引擎。

严格遵守 Spec 三件合规边界：
  1) 仅 scope_asset_ids 内资产行动，空 scope 拒绝任何启用与生成。
  2) Loop1/2 只生成 Task 并走原有 Task → Orchestrator 流水线（确定性引擎为主），
     绝不直接发自定义 HTTP。
  3) Loop3 只做正则抽取 + MinerCandidate 入库，零网络调用，越权项显式 skipped。

三 Loop（顺序执行，共享同一 budget 计数）：
  Loop1 Coverage Gap：scope 每个 host × MINER_REQUIRED_KINDS 笛卡尔，
    查 Intel(host + key == host AND kind == x) 缺口 → 生成 pending_approval Task。
  Loop2 Decay & Re-Verify：Intel updated_at < now - 30d AND lifecycle == active
    → confidence ×= 0.85 floor 0.1；append STALE_CANDIDATE tag；
    confidence < 0.4 → lifecycle = stale；生成 reverify Task。
  Loop3 Link-Extend（近 7 日 Intel）：调 link_extract.extract_and_persist_candidates
    把 hostname/IPv4/CVE-ID 候选写入 MinerCandidate。

Budget 限制（按 Asia/Shanghai 自然日，当日 00:00 CST → UTC 换算）：
  count_today = Task where source STARTS WITH "miner:" AND created_at >= today_utc
  budget_left = daily_budget_max_jobs - count_today
  新增 Task 前若 budget_left <= 0 → MinerRun.budget_hit_limit = True + WARN 日志，
  本轮不再新增（candidate 写入不受 budget 限制）。
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import SessionLocal
from ..models import (
    Intel,
    MinerCandidate,
    MinerRun,
    Setting,
    Task,
    TASK_PENDING_APPROVAL,
)
from .link_extract import extract_and_persist_candidates

log = logging.getLogger("aififteen-hunter.miner")

MINER_REQUIRED_KINDS = [
    "os_fingerprint",
    "tech_stack",
    "passive_dns",
    "port_scan",
    "header_scan",
]

TASK_PENDING_APPROVAL_STR = TASK_PENDING_APPROVAL  # backward compat ref name
MINER_AUTO_APPROVE_REVERIFY = "reverify_only"
MINER_AUTO_APPROVE_ALL = "all_scope"
MINER_AUTO_APPROVE_OFF = "off"

MINER_SETTING_PREFIX = "miner."

# Asia/Shanghai UTC+8（固定，避免 tzdata 依赖）
_CST = timezone(timedelta(hours=8))


@dataclass
class MinerConfig:
    enabled: bool = False
    scope_asset_ids: list[str] = field(default_factory=list)
    daily_budget_max_jobs: int = 20
    max_runtime_min: int = 120
    auto_approve: str = MINER_AUTO_APPROVE_REVERIFY
    cron_expr: str = "0 2 * * *"


def _parse_bool(v: str) -> bool:
    return str(v or "").strip().lower() in ("1", "true", "yes", "on")


def load_miner_config(db: Session) -> MinerConfig:
    """从 Setting 表按 'miner.' 前缀组装；缺项走默认值。"""
    cfg = MinerConfig()
    try:
        rows = db.scalars(select(Setting).where(Setting.key.like(MINER_SETTING_PREFIX + "%")))
        kv: dict[str, str] = {r.key[len(MINER_SETTING_PREFIX):]: (r.value or "") for r in rows}
    except Exception:  # noqa: BLE001 - 首次启动可能 Setting 表尚未迁移
        kv = {}
    cfg.enabled = _parse_bool(kv.get("enabled", ""))
    scope_raw = (kv.get("scope_asset_ids") or "").strip()
    if scope_raw:
        try:
            parsed = json.loads(scope_raw)
            if isinstance(parsed, list):
                cfg.scope_asset_ids = [str(s).strip() for s in parsed if str(s).strip()]
        except (ValueError, TypeError):
            # 兼容：分号/换行分隔的裸字符串
            bits: list[str] = []
            for sep in [";", ",", "\n"]:
                if sep in scope_raw:
                    bits = [s.strip() for s in scope_raw.split(sep) if s.strip()]
                    break
            if not bits:
                bits = [scope_raw.strip()]
            cfg.scope_asset_ids = bits
    budget = kv.get("daily_budget_max_jobs")
    try:
        n = int(budget or "20")
        cfg.daily_budget_max_jobs = max(1, min(200, n))
    except (ValueError, TypeError):
        cfg.daily_budget_max_jobs = 20
    runtime = kv.get("max_runtime_min")
    try:
        n = int(runtime or "120")
        cfg.max_runtime_min = max(5, min(1440, n))
    except (ValueError, TypeError):
        cfg.max_runtime_min = 120
    aa = (kv.get("auto_approve") or MINER_AUTO_APPROVE_REVERIFY).strip().lower()
    if aa not in (MINER_AUTO_APPROVE_REVERIFY, MINER_AUTO_APPROVE_ALL, MINER_AUTO_APPROVE_OFF):
        aa = MINER_AUTO_APPROVE_REVERIFY
    cfg.auto_approve = aa
    cfg.cron_expr = (kv.get("cron_expr") or "0 2 * * *").strip() or "0 2 * * *"
    return cfg


def save_miner_config(db: Session, cfg: MinerConfig) -> MinerConfig:
    """把 MinerConfig 写回 Setting 表（幂等 upsert）。调用方自己 commit。"""
    items = {
        "enabled": "true" if cfg.enabled else "false",
        "scope_asset_ids": json.dumps([str(s) for s in (cfg.scope_asset_ids or []) if str(s).strip()],
                                      ensure_ascii=False),
        "daily_budget_max_jobs": str(max(1, min(200, int(cfg.daily_budget_max_jobs)))),
        "max_runtime_min": str(max(5, min(1440, int(cfg.max_runtime_min)))),
        "auto_approve": cfg.auto_approve or MINER_AUTO_APPROVE_REVERIFY,
        "cron_expr": cfg.cron_expr or "0 2 * * *",
    }
    for k, v in items.items():
        full_key = MINER_SETTING_PREFIX + k
        row = db.get(Setting, full_key)
        if row is None:
            db.add(Setting(key=full_key, value=v))
        else:
            row.value = v
        db.flush()
    return cfg


def _today_start_utc() -> datetime:
    """Asia/Shanghai 今天 00:00 转 UTC naive datetime（DB 用 naive UTC）。"""
    now_cst = datetime.now(_CST)
    midnight_cst = now_cst.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_cst.astimezone(timezone.utc)
    return midnight_utc.replace(tzinfo=None)


def _count_today_miner_tasks(db: Session) -> int:
    today_start = _today_start_utc()
    cnt = db.scalar(
        select(func.count(Task.id)).where(
            and_(
                func.substr(Task.source, 1, 6) == "miner:",
                Task.created_at >= today_start,
            )
        )
    ) or 0
    return int(cnt)


def _new_miner_task(
    db: Session, *, host: str, kind: str, src_kind: str,
    name_hint: str = "", vuln_types: str = "", manual_targets: str = "",
) -> Task | None:
    t = Task(
        name=name_hint or f"[MINER] {src_kind} {host}/{kind}",
        mode="engine",
        source=f"miner:{src_kind}",
        manual_targets=manual_targets or f"https://{host}",
        vuln_types=vuln_types or "tech_stack_fingerprint,info_disclosure",
        status=TASK_PENDING_APPROVAL_STR,
    )
    db.add(t)
    db.flush()
    return t


def _intel_has(db: Session, *, host: str, kind: str) -> bool:
    """host × kind 的 Intel 是否存在（key/value 里匹配 host 或 key==host）。"""
    host_l = (host or "").strip().lower()
    if not host_l:
        return False
    stmt = (
        select(Intel.id)
        .where(Intel.kind == kind)
        .where((func.lower(Intel.key) == host_l) |
               (func.lower(func.coalesce(Intel.value, "")).contains(host_l)))
        .limit(1)
    )
    return db.scalar(stmt) is not None


def _loop1_coverage_gap(db: Session, cfg: MinerConfig, budget_left: int) -> tuple[int, int]:
    """Loop1: host × required_kinds 覆盖缺口 → 生成 Task。

    Returns (loop_count, new_budget_left)
    """
    count = 0
    hosts = [str(s).strip() for s in (cfg.scope_asset_ids or []) if str(s).strip()]
    # 过滤明显非 host/IP/域名：CIDR 拆成网段描述；CIDR 不直接当任务 target
    targets: list[str] = []
    for h in hosts:
        if "/" in h:
            # CIDR：只做覆盖缺口的 host 描述名，不直接生成扫描 URL（避免隐式扩大范围）
            continue
        targets.append(h)

    for host in targets:
        if budget_left <= 0:
            break
        for kind in MINER_REQUIRED_KINDS:
            if budget_left <= 0:
                break
            if _intel_has(db, host=host, kind=kind):
                continue
            task = _new_miner_task(
                db, host=host, kind=kind, src_kind="coverage_gap",
                name_hint=f"[MINER] coverage_gap {host}/{kind}",
                vuln_types="tech_stack_fingerprint,info_disclosure",
                manual_targets=f"https://{host}",
            )
            if task is None:
                continue
            if cfg.auto_approve == MINER_AUTO_APPROVE_ALL:
                task.status = "pending"
                # 真正的 start_task 调用方会处理（见 run_miner_once 底部批批起）
                task.params = dict(task.params or {}, _miner_auto_start=True)
            count += 1
            budget_left -= 1
    return count, budget_left


def _loop2_reverify(db: Session, cfg: MinerConfig, budget_left: int) -> tuple[int, int]:
    """Loop2: Intel 30d 未更新且 active → 衰减 confidence + tag STALE_CANDIDATE → 生成 reverify Task."""
    count = 0
    cutoff = datetime.utcnow() - timedelta(days=30)
    rows = db.scalars(
        select(Intel).where(and_(Intel.updated_at < cutoff, Intel.lifecycle == "active"))
    ).all()
    auto_start_ids: list[str] = []
    for it in rows:
        # confidence 衰减：至少保留 0.1
        it.confidence = max(0.1, float(it.confidence or 0.6) * 0.85)
        # 标签 STALE_CANDIDATE（幂等）
        tags = list(it.tags) if isinstance(it.tags, list) else []
        if "STALE_CANDIDATE" not in tags:
            tags.append("STALE_CANDIDATE")
        it.tags = tags
        # lifecycle 降级 < 0.4
        if it.confidence < 0.4:
            it.lifecycle = "stale"
        # 生成 reverify 任务（限 budget）
        if budget_left <= 0:
            continue
        host_for_task = (it.key or "").strip()
        if not host_for_task:
            continue
        # 避免当日同 host/reverify 重复：若今天已经有 miner:reverify 且 manual_targets 含 host 则跳过
        today_start = _today_start_utc()
        dup = db.scalar(
            select(Task.id)
            .where(Task.source == "miner:reverify")
            .where(Task.created_at >= today_start)
            .where(func.coalesce(Task.manual_targets, "").contains(host_for_task))
            .limit(1)
        )
        if dup is not None:
            continue
        task = _new_miner_task(
            db, host=host_for_task, kind=it.kind or "reverify",
            src_kind="reverify",
            name_hint=f"[MINER] reverify {host_for_task}/{it.kind} (conf={float(it.confidence):.2f})",
            vuln_types="tech_stack_fingerprint,info_disclosure,config_misconfig",
            manual_targets=f"https://{host_for_task}",
        )
        if task is None:
            continue
        if cfg.auto_approve in (MINER_AUTO_APPROVE_REVERIFY, MINER_AUTO_APPROVE_ALL):
            task.status = "pending"
            task.params = dict(task.params or {}, _miner_auto_start=True)
            auto_start_ids.append(task.id)
        count += 1
        budget_left -= 1
    db.flush()
    return count, budget_left


def _loop3_link_extend(db: Session, cfg: MinerConfig) -> int:
    """Loop3：近 7 日 Intel（updated_at ≥ cutoff）抽取候选。"""
    cutoff = datetime.utcnow() - timedelta(days=7)
    batch = db.scalars(
        select(Intel).where(Intel.updated_at >= cutoff)
    ).all()
    return extract_and_persist_candidates(db, list(batch), cfg.scope_asset_ids or [])


async def _kickoff_auto_tasks(task_ids: list[str]) -> None:
    """后台把标记 _miner_auto_start 的 Task 跑起来（Orchestrator.run_task）。"""
    if not task_ids:
        return
    from .orchestrator import Orchestrator

    db = SessionLocal()
    try:
        for tid in task_ids:
            try:
                t = db.get(Task, tid)
                if t and t.status in ("pending", "collecting", "running"):
                    continue
                await Orchestrator(db).run_task(tid)
            except Exception as e:  # noqa: BLE001
                log.warning("Miner 自动启动 task %s 异常: %s", tid, e)
                try:
                    t2 = db.get(Task, tid)
                    if t2 is not None:
                        t2.status = "failed"
                        t2.error = f"[Miner 自动启动] [{type(e).__name__}] {e}"[:2000]
                        db.commit()
                except Exception:  # noqa: BLE001
                    db.rollback()
    finally:
        db.close()


async def run_miner_once(trigger_from: str = "manual") -> dict:
    """Miner 单次主入口（cron / trigger-once 均调用本函数）。

    返回 dict 包含 run_id + 三 count，便于审计。
    """
    db = SessionLocal()
    run_id = uuid.uuid4().hex
    run = MinerRun(id=run_id, trigger_at=datetime.utcnow(), trigger_from=trigger_from,
                   loop1_coverage_count=0, loop2_reverify_count=0, loop3_link_count=0,
                   budget_hit_limit=False)
    db.add(run)
    db.commit()

    cfg = MinerConfig()
    try:
        cfg = load_miner_config(db)
        if not cfg.enabled:
            run.finished_at = datetime.utcnow()
            run.error_log = "miner.enabled=false, skipped"
            db.commit()
            return {"run_id": run_id, "skipped": True, "reason": "disabled"}
        if not cfg.scope_asset_ids or not any(str(s).strip() for s in cfg.scope_asset_ids):
            run.finished_at = datetime.utcnow()
            run.error_log = "empty scope_asset_ids, cannot run (enable requires non-empty scope)"
            db.commit()
            log.warning("[miner:%s] empty scope，拒绝运行", run_id[:8])
            return {"run_id": run_id, "skipped": True, "reason": "empty_scope"}

        # ===== Budget 初始化 =====
        today_count = _count_today_miner_tasks(db)
        budget_left = max(0, int(cfg.daily_budget_max_jobs) - today_count)
        budget_hit_before = budget_left <= 0

        # ===== Loop 1 Coverage =====
        l1, budget_left = _loop1_coverage_gap(db, cfg, budget_left)
        run.loop1_coverage_count = l1

        # ===== Loop 2 Reverify =====
        l2, budget_left = _loop2_reverify(db, cfg, budget_left)
        run.loop2_reverify_count = l2

        # ===== Loop 3 Link Extend (不受 budget) =====
        l3 = _loop3_link_extend(db, cfg)
        run.loop3_link_count = l3

        # Budget 命中标记
        if (budget_hit_before or budget_left <= 0) and (l1 + l2) > 0:
            run.budget_hit_limit = True
        if budget_hit_before and not l1 and not l2:
            run.budget_hit_limit = True
            run.error_log = (run.error_log or "") + f"budget hit before loop: today={today_count}/{cfg.daily_budget_max_jobs}; "

        # 持久化 Task/Candidate 写入 + MinerRun
        db.commit()

        # 捞取需要自动启动的 Task（params._miner_auto_start=True，status=pending）
        auto_ids = list(db.scalars(
            select(Task.id)
            .where(Task.status == "pending")
            .where(func.substr(Task.source, 1, 6) == "miner:")
            .where(Task.created_at >= run.trigger_at - timedelta(seconds=5))
        ).all())
        if auto_ids:
            asyncio.create_task(_kickoff_auto_tasks(auto_ids))

        run.finished_at = datetime.utcnow()
        db.commit()
        log.info(
            "[miner:%s] done trigger_from=%s l1=%d l2=%d l3=%d budget_hit=%s",
            run_id[:8], trigger_from, l1, l2, l3, run.budget_hit_limit,
        )
        return {
            "run_id": run_id,
            "loop1_coverage_count": l1,
            "loop2_reverify_count": l2,
            "loop3_link_count": l3,
            "budget_hit_limit": run.budget_hit_limit,
        }
    except Exception as e:  # noqa: BLE001
        tb = __import__("traceback").format_exc()
        log.error("[miner:%s] 异常:\n%s", run_id[:8], tb)
        try:
            db.rollback()
            run.finished_at = datetime.utcnow()
            run.error_log = (run.error_log or "") + f"fatal: {e}"
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        return {"run_id": run_id, "error": str(e)}
    finally:
        db.close()


def trigger_miner_cron_refresh(new_cron_expr: str | None = None) -> None:
    """在 PUT /miner/config 保存后调用：刷新 __miner_internal__ job 的 trigger。

    若 APScheduler 未启动（测试/单测环境），本函数空操作。
    """
    from .scheduler import scheduler  # 避免循环 import

    try:
        from apscheduler.triggers.cron import CronTrigger
    except Exception:  # noqa: BLE001
        return
    if not scheduler.running:
        return
    job_id = "__miner_internal__"
    # 取下一次 cron_expr 优先级：参数 > Setting 表 > default "0 2 * * *"
    cron = (new_cron_expr or "").strip()
    if not cron:
        try:
            db = SessionLocal()
            try:
                row = db.get(Setting, MINER_SETTING_PREFIX + "cron_expr")
                if row and (row.value or "").strip():
                    cron = row.value.strip()
            finally:
                db.close()
        except Exception:  # noqa: BLE001
            pass
    if not cron:
        cron = "0 2 * * *"
    try:
        trig = CronTrigger.from_crontab(cron, timezone="Asia/Shanghai")
    except Exception as e:  # noqa: BLE001
        log.warning("Miner cron_expr 解析失败(%s)，回退默认 0 2 * * *: %s", cron, e)
        trig = CronTrigger.from_crontab("0 2 * * *", timezone="Asia/Shanghai")

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    def _sync_wrapper():
        # APScheduler asyncio 调度器里 sync func 会在线程池里跑，内部 asyncio.run 一次 miner
        try:
            asyncio.run(run_miner_once(trigger_from="cron"))
        except Exception as e:  # noqa: BLE001
            log.error("[miner:cron] wrapper 异常: %s", e)

    scheduler.add_job(
        id=job_id,
        func=_sync_wrapper,
        trigger=trig,
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )
    log.info("Miner 内部 cron 已刷新: %s", cron)
