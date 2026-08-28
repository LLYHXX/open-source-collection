"""情报库路由：列表 / 退役（记忆沉淀的可视化管理）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import Intel
from ..schemas import IntelOut, StandardResponse

router = APIRouter(prefix="/intel", tags=["intel"], dependencies=[Depends(verify_token)])


@router.get("", response_model=list[IntelOut])
def list_intel(kind: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Intel).order_by(Intel.updated_at.desc())
    if kind:
        stmt = stmt.where(Intel.kind == kind)
    return list(db.scalars(stmt.limit(200)))


@router.delete("/{intel_id}", response_model=StandardResponse)
def retire_intel(intel_id: str, db: Session = Depends(get_db)):
    it = db.get(Intel, intel_id)
    if not it:
        raise HTTPException(404, "情报不存在")
    it.lifecycle = "retired"
    db.commit()
    return StandardResponse(message="已退役")
