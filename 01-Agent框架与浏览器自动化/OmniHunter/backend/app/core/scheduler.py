"""定时任务调度：APScheduler 周期触发，自动新建任务并运行，期限到期自停。

启动→执行→关闭循环：每次触发按 task_template 生成新 Task，后台跑完整流水线，
跑完等待下次触发；到达 deadline（默认1月）自动停用，前端可延长期限或重新启用。
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from ..database import SessionLocal
from ..models import Schedule, Task

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
    except Exception:  # noqa: BLE001 后台任务异常不破坏调度
        db.rollback()
        # 把卡在 collecting/running 的 Task 标记为 failed，防止状态不一致
        task = db.get(Task, task_id)
        if task and task.status in ("collecting", "running"):
            task.status = "failed"
            db.commit()
    finally:
        db.close()
