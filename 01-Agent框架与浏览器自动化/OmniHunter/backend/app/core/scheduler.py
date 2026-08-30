"""定时任务调度：APScheduler 周期触发，自动新建任务并运行，期限到期自停。

启动→执行→关闭循环：每次触发按 task_template 生成新 Task，后台跑完整流水线，
跑完等待下次触发；到达 deadline（默认1月）自动停用，前端可延长期限或重新启用。
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from ..database import SessionLocal
from ..models import Schedule, Task

log = logging.getLogger("aififteen-hunter")

# 时区固定 Asia/Shanghai，与用户本地一致
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def _build_trigger(sch: Schedule):
    """cron 优先，无 cron 用间隔分钟。"""
    if sch.cron_expr:
        try:
            return CronTrigger.from_crontab(sch.cron_expr)
        except Exception:  # noqa: BLE001 cron 解析失败则回退间隔
            pass
    minutes = sch.interval_minutes or 1440
    return IntervalTrigger(minutes=minutes)


def _sync_next_run(sch: Schedule) -> None:
    job = scheduler.get_job(sch.id)
    if job and job.next_run_time:
        # APScheduler 用 tz-aware，DB 存 naive，去掉 tzinfo
        sch.next_run = job.next_run_time.replace(tzinfo=None)


def add_schedule_job(sch: Schedule) -> None:
    """把 schedule 加进调度器（已存在则替换）。"""
    if sch.id and scheduler.get_job(sch.id):
        scheduler.remove_job(sch.id)
    scheduler.add_job(
        run_scheduled_task, _build_trigger(sch),
        id=sch.id, args=[sch.id],
        replace_existing=True,
    )
    _sync_next_run(sch)


def remove_schedule_job(schedule_id: str) -> None:
    try:
        scheduler.remove_job(schedule_id)
    except Exception:  # noqa: BLE001 任务不存在即忽略
        pass


def init_scheduler() -> None:
    """启动时调用：载入所有 enabled 且未过期的 schedule 并启动调度器。"""
    db = SessionLocal()
    try:
        schs = db.scalars(select(Schedule).where(Schedule.enabled.is_(True))).all()
        now = datetime.utcnow()
        for sch in schs:
            if sch.deadline and now > sch.deadline:
                # 期限已过：自动停用
                sch.enabled = False
                continue
            add_schedule_job(sch)
        db.commit()
    finally:
        db.close()
    if not scheduler.running:
        scheduler.start()

    # ===== Miner 内部 cron job：默认每日 02:00 CST；Setting 表 miner.cron_expr 可覆盖 =====
    try:
        from apscheduler.triggers.cron import CronTrigger
        from .miner import MINER_SETTING_PREFIX, run_miner_once
        from ..models import Setting
        from ..config import get_settings as _gs

        # 读优先级：Setting 表 > env Settings.miner_cron_expr
        miner_cron = ""
        try:
            _db = SessionLocal()
            try:
                row = _db.get(Setting, MINER_SETTING_PREFIX + "cron_expr")
                if row and (row.value or "").strip():
                    miner_cron = row.value.strip()
            finally:
                _db.close()
        except Exception:  # noqa: BLE001
            miner_cron = ""
        if not miner_cron:
            try:
                miner_cron = getattr(_gs(), "miner_cron_expr", None) or ""
            except Exception:  # noqa: BLE001
                miner_cron = ""
        if not miner_cron:
            miner_cron = "0 2 * * *"

        try:
            _trig = CronTrigger.from_crontab(miner_cron, timezone="Asia/Shanghai")
        except Exception as _e:  # noqa: BLE001
            import logging as _log
            _log.getLogger("aififteen-hunter").warning(
                "Miner cron 解析失败(%s)，回退 0 2 * * *: %s", miner_cron, _e
            )
            miner_cron = "0 2 * * *"
            _trig = CronTrigger.from_crontab(miner_cron, timezone="Asia/Shanghai")

        def __miner_sync_wrapper():
            """APScheduler asyncio 调度器里的 sync wrapper：在线程池里 asyncio.run。"""
            try:
                asyncio.run(run_miner_once(trigger_from="cron"))
            except Exception as _e:  # noqa: BLE001
                import logging as _log2
                _log2.getLogger("aififteen-hunter").error(
                    "[miner:cron] wrapper 异常: %s", _e
                )

        scheduler.add_job(
            id="__miner_internal__",
            func=__miner_sync_wrapper,
            trigger=_trig,
            replace_existing=True,
            misfire_grace_time=3600,
            coalesce=True,
            max_instances=1,
        )
        import logging as _l
        _l.getLogger("aififteen-hunter").info(
            "Miner 内部 cron 已挂载: __miner_internal__ cron=%s", miner_cron
        )
    except Exception as e:  # noqa: BLE001
        import logging as _l2
        _l2.getLogger("aififteen-hunter").warning(
            "Miner 内部 cron 挂载失败（首次启动模型未就绪可忽略）: %s", e
        )

    # ===== CVE 库定时任务：每日拉取 + 自动扫描（可配置开关）=====
    _register_cve_jobs()


async def run_scheduled_task(schedule_id: str) -> None:
    """周期触发：新建 Task → 后台跑流水线 → 更新调度元数据。"""
    db = SessionLocal()
    try:
        sch = db.get(Schedule, schedule_id)
        if not sch or not sch.enabled:
            return
        now = datetime.utcnow()
        # 期限到期：自动停用并移除调度
        if sch.deadline and now > sch.deadline:
            sch.enabled = False
            remove_schedule_job(schedule_id)
            db.commit()
            return

        # 按 task_template 生成新 Task
        template = dict(sch.task_template or {})
        run_no = sch.run_count + 1
        task = Task(
            name=f"{sch.name} #{run_no} ({now.strftime('%m-%d %H:%M')})",
            mode=template.get("mode", "EduSRC"),
            vuln_types=template.get("vuln_types", ""),
            source=template.get("source", "manual"),
            collect_method=template.get("collect_method", "auto"),
            collect_query=template.get("collect_query", ""),
            manual_targets=template.get("manual_targets", ""),
            max_pages=template.get("max_pages", 3),
            llm_override=template.get("llm_override", {}),
            fofa_override=template.get("fofa_override", ""),
        )
        db.add(task)
        sch.last_run = now
        sch.run_count = run_no
        _sync_next_run(sch)
        db.commit()

        # 后台跑完整流水线（启动→执行→关闭），不阻塞调度线程
        asyncio.create_task(_run_orchestrator(task.id))
    finally:
        db.close()


async def _run_orchestrator(task_id: str) -> None:
    from .orchestrator import Orchestrator

    db = SessionLocal()
    try:
        await Orchestrator(db).run_task(task_id)
    except Exception as e:  # noqa: BLE001 后台任务异常不破坏调度
        db.rollback()
        # 把卡在 collecting/running 的 Task 标记为 failed + error，防止状态不一致
        task = db.get(Task, task_id)
        if task is not None:
            task.status = "failed"
            task.error = f"[定时调度后台] [{type(e).__name__}] {e}"[:2000]
            try:
                db.commit()
            except Exception:  # noqa: BLE001
                db.rollback()
    finally:
        db.close()


# ===== CVE 定时任务：每日自动拉取 CVE + 自动扫描可配置开关 =====
async def run_cve_fetch_job() -> None:
    """CVE 库自动拉取：每日凌晨执行，读取 settings.cve_fetch_days 拉取最近 N 天。"""
    from ..config import get_settings
    from ..tools.cve_fetcher import fetch_and_update_cves

    settings = get_settings()
    if not getattr(settings, "cve_fetch_enabled", True):
        return
    db = SessionLocal()
    try:
        result = await fetch_and_update_cves(
            settings, db,
            days=getattr(settings, "cve_fetch_days", 7),
            source="all",
        )
        added = result.get("added", 0)
        updated = result.get("updated", 0)
        log.info("[CVE:cron] 自动拉取完成：新增 %d，更新 %d", added, updated)
    except Exception as e:  # noqa: BLE001
        log.warning("[CVE:cron] 自动拉取异常: %s", e)
    finally:
        db.close()


async def run_cve_auto_scan_job() -> None:
    """CVE 自动扫描：对配置时间段内新增的 pending 命中资产跑挖掘流水线。

    仅在 cve_auto_scan_enabled=True 时执行；有副作用（向目标发请求），
    故默认关闭，用户在 Settings 页开启。
    单次扫描资产数受 cve_auto_scan_max 限制防失控。
    """
    from sqlalchemy import select

    from ..config import get_settings
    from ..models import CveAssetHit, Task

    settings = get_settings()
    if not getattr(settings, "cve_auto_scan_enabled", False):
        return

    db = SessionLocal()
    try:
        # 取 pending 资产，按创建时间排序，限制单次扫描数量
        max_scan = int(getattr(settings, "cve_auto_scan_max", 10))
        hits = db.scalars(
            select(CveAssetHit)
            .where(CveAssetHit.scan_status == "pending")
            .order_by(CveAssetHit.created_at.asc())
            .limit(max_scan)
        ).all()
        if not hits:
            log.info("[CVE:cron] 自动扫描跳过：无 pending 命中资产")
            return

        pipeline = getattr(settings, "cve_auto_scan_pipeline", "engine")
        urls = [h.url for h in hits if h.url]
        if not urls:
            return

        task = Task(
            name=f"CVE 自动扫描 {datetime.utcnow().strftime('%m-%d %H:%M')} "
                 f"({len(urls)} 个资产)",
            mode="engine" if pipeline == "engine" else "EduSRC",
            source="cve",
            manual_targets="\n".join(urls),
            status="running",
        )
        db.add(task)
        for h in hits:
            h.task_id = task.id
            h.scan_status = "scanning"
        db.commit()
        task_id = task.id
        hit_ids = [h.id for h in hits]
        log.info("[CVE:cron] 启动自动扫描 task=%s, %d 个资产, pipeline=%s",
                 task_id, len(hit_ids), pipeline)
    except Exception as e:  # noqa: BLE001
        log.warning("[CVE:cron] 自动扫描准备失败: %s", e)
        db.rollback()
        return
    finally:
        db.close()

    # 后台跑流水线
    async def _bg():
        db2 = SessionLocal()
        try:
            from .orchestrator import Orchestrator
            orch = Orchestrator(db2)
            task = db2.get(Task, task_id)
            if not task:
                return
            for hit_id in hit_ids:
                hit = db2.get(CveAssetHit, hit_id)
                if not hit or not hit.url:
                    continue
                try:
                    if pipeline == "engine":
                        await orch.run_engine_pipeline(task, hit.url)
                    elif pipeline == "collab":
                        await orch.run_collab_pipeline(task, hit.url)
                    elif pipeline == "traffic":
                        await orch.run_traffic_pipeline(task, hit.url)
                    hit.scan_status = "done"
                except Exception as e:  # noqa: BLE001
                    hit.scan_status = "failed"
                    log.warning("[CVE:cron] 扫描失败 %s: %s", hit.url, e)
                db2.commit()
            task.status = "review"
            db2.commit()
        except Exception as e:  # noqa: BLE001
            log.warning("[CVE:cron] 扫描任务异常: %s", e)
            db2.rollback()
        finally:
            db2.close()

    asyncio.create_task(_bg())


def _register_cve_jobs() -> None:
    """挂载 CVE 定时任务到调度器（init_scheduler 时调用）。

    两个独立 job：
      - cve_fetcher：每日拉取最近 N 天 CVE（默认 02:00）
      - cve_auto_scan：每日扫描 pending 命中资产（默认 03:00，副作用默认关）
    cron 表达式从 settings 读取，支持动态配置覆盖。
    """
    from ..config import get_settings as _gs

    try:
        settings = _gs()
        # 1) CVE 拉取任务
        fetch_cron = getattr(settings, "cve_fetch_cron", "0 2 * * *") or "0 2 * * *"
        try:
            fetch_trig = CronTrigger.from_crontab(fetch_cron, timezone="Asia/Shanghai")
        except Exception as _e:  # noqa: BLE001
            log.warning("CVE fetch cron 解析失败(%s)，回退 0 2 * * *: %s", fetch_cron, _e)
            fetch_cron = "0 2 * * *"
            fetch_trig = CronTrigger.from_crontab(fetch_cron, timezone="Asia/Shanghai")

        async def _cve_fetch_wrapper():
            try:
                await run_cve_fetch_job()
            except Exception as _e:  # noqa: BLE001
                log.error("[CVE:cron] fetch wrapper 异常: %s", _e)

        scheduler.add_job(
            id="__cve_fetcher__",
            func=_cve_fetch_wrapper,
            trigger=fetch_trig,
            replace_existing=True,
            misfire_grace_time=3600,
            coalesce=True,
            max_instances=1,
        )

        # 2) CVE 自动扫描任务
        scan_cron = getattr(settings, "cve_auto_scan_cron", "0 3 * * *") or "0 3 * * *"
        try:
            scan_trig = CronTrigger.from_crontab(scan_cron, timezone="Asia/Shanghai")
        except Exception as _e:  # noqa: BLE001
            log.warning("CVE auto scan cron 解析失败(%s)，回退 0 3 * * *: %s", scan_cron, _e)
            scan_cron = "0 3 * * *"
            scan_trig = CronTrigger.from_crontab(scan_cron, timezone="Asia/Shanghai")

        async def _cve_scan_wrapper():
            try:
                await run_cve_auto_scan_job()
            except Exception as _e:  # noqa: BLE001
                log.error("[CVE:cron] auto scan wrapper 异常: %s", _e)

        scheduler.add_job(
            id="__cve_auto_scan__",
            func=_cve_scan_wrapper,
            trigger=scan_trig,
            replace_existing=True,
            misfire_grace_time=3600,
            coalesce=True,
            max_instances=1,
        )
        log.info("CVE 定时任务已挂载: fetch=%s, auto_scan=%s (enabled=%s)",
                 fetch_cron, scan_cron,
                 getattr(settings, "cve_auto_scan_enabled", False))
    except Exception as e:  # noqa: BLE001
        log.warning("CVE 定时任务挂载失败（首次启动可忽略）: %s", e)
