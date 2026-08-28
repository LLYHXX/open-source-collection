"""定时任务路由：CRUD + 延期 + 启停。

期限默认1月，到期自动停用；可延期（延长到1月以后）或重新启用。
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..core.scheduler import (
    add_schedule_job,
    init_scheduler,
    remove_schedule_job,
    scheduler,
)
from ..database import get_db
from ..models import Schedule
from ..schemas import ScheduleCreate, ScheduleExtend, ScheduleOut, StandardResponse

router = APIRouter(prefix="/schedules", tags=["schedules"],
                   dependencies=[Depends(verify_token)])


@router.post("", response_model=StandardResponse)
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db)):
    sch = Schedule(
        name=payload.name,
        task_template=payload.task_template,
        cron_expr=payload.cron_expr,
        interval_minutes=payload.interval_minutes,
        deadline=datetime.utcnow() + timedelta(days=payload.deadline_days),
    )
    db.add(sch)
    db.commit()
    db.refresh(sch)
    # 调度器未启动则启动（保证非 lifespan 场景也能用）
    if not scheduler.running:
        init_scheduler()
    add_schedule_job(sch)
    db.commit()
    return StandardResponse(message="定时任务已创建", data={"id": sch.id})


@router.get("", response_model=list[ScheduleOut])
def list_schedules(db: Session = Depends(get_db)):
    return list(db.scalars(select(Schedule).order_by(Schedule.created_at.desc())))


@router.post("/{schedule_id}/extend", response_model=StandardResponse)
def extend_schedule(schedule_id: str, payload: ScheduleExtend,
                    db: Session = Depends(get_db)):
    """延长期限（延长到当前期限之后 extend_days 天）。

    若已因到期停用，延期后自动重新启用并恢复调度。
    """
    sch = db.get(Schedule, schedule_id)
    if not sch:
        raise HTTPException(404, "定时任务不存在")
    base = sch.deadline or datetime.utcnow()
    if base < datetime.utcnow():
        base = datetime.utcnow()
    sch.deadline = base + timedelta(days=payload.extend_days)
    if not sch.enabled:
        sch.enabled = True
        if scheduler.running:
            add_schedule_job(sch)
    db.commit()
    return StandardResponse(
        message=f"期限已延长 {payload.extend_days} 天，新期限 {sch.deadline}",
        data={"deadline": str(sch.deadline)},
    )


@router.post("/{schedule_id}/toggle", response_model=StandardResponse)
def toggle_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """启用/停用切换：启动→关闭→启动 循环由前端按钮触发。"""
    sch = db.get(Schedule, schedule_id)
    if not sch:
        raise HTTPException(404, "定时任务不存在")
    if sch.enabled:
        sch.enabled = False
        remove_schedule_job(schedule_id)
        msg = "已停用"
    else:
        if sch.deadline and sch.deadline < datetime.utcnow():
            raise HTTPException(400, "期限已过，请先延期再启用")
        sch.enabled = True
        if not scheduler.running:
            init_scheduler()
        add_schedule_job(sch)
        msg = "已启用"
    db.commit()
    return StandardResponse(message=msg, data={"enabled": sch.enabled})


@router.post("/{schedule_id}/run", response_model=StandardResponse)
async def run_now(schedule_id: str, db: Session = Depends(get_db)):
    """手动立即触发一次（不等周期）。"""
    from ..core.scheduler import run_scheduled_task
    import asyncio
    sch = db.get(Schedule, schedule_id)
    if not sch:
        raise HTTPException(404, "定时任务不存在")
    asyncio.create_task(run_scheduled_task(schedule_id))
    return StandardResponse(message="已触发一次执行")


@router.delete("/{schedule_id}", response_model=StandardResponse)
def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    sch = db.get(Schedule, schedule_id)
    if not sch:
        raise HTTPException(404, "定时任务不存在")
    remove_schedule_job(schedule_id)
    db.delete(sch)
    db.commit()
    return StandardResponse(message="已删除")
