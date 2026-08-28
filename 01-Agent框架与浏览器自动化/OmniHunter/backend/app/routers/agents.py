"""Agent 路由：运行列表 + 事件流（控制台实时看板数据源）。"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import AgentMessage, AgentRun, Target
from ..schemas import AgentMessageOut

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[Depends(verify_token)])


@router.get("/runs")
def list_runs(task_id: str | None = None, db: Session = Depends(get_db)):
    stmt = select(AgentRun).order_by(AgentRun.started_at.desc())
    if task_id:
        target_ids = [
            t.id for t in db.scalars(select(Target).where(Target.task_id == task_id)).all()
        ]
        if not target_ids:
            return []
        stmt = stmt.where(AgentRun.target_id.in_(target_ids))
    runs = list(db.scalars(stmt.limit(100)))
    return [
        {
            "id": r.id,
            "target_id": r.target_id,
            "role": r.agent_role,
            "status": r.status,
            "stage": r.stage,
            "step": r.step,
            "summary": r.summary,
        }
        for r in runs
    ]


@router.get("/messages", response_model=list[AgentMessageOut])
def list_messages(run_id: str | None = None, target_id: str | None = None,
                 db: Session = Depends(get_db)):
    stmt = select(AgentMessage).order_by(AgentMessage.created_at.asc())
    if run_id:
        stmt = stmt.where(AgentMessage.run_id == run_id)
    if target_id:
        stmt = stmt.where(AgentMessage.target_id == target_id)
    return list(db.scalars(stmt.limit(500)))
