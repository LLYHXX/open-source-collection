"""漏洞路由：列表 + 人工复审裁决（通过/打回/编辑/标记提交）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import Vuln
from ..schemas import StandardResponse, VulnOut, VulnReview

router = APIRouter(prefix="/vulns", tags=["vulns"], dependencies=[Depends(verify_token)])


@router.get("", response_model=list[VulnOut])
def list_vulns(task_id: str | None = None, status: str | None = None,
               db: Session = Depends(get_db)):
    stmt = select(Vuln).order_by(Vuln.created_at.desc())
    if task_id:
        stmt = stmt.where(Vuln.task_id == task_id)
    if status:
        stmt = stmt.where(Vuln.status == status)
    return list(db.scalars(stmt.limit(300)))


@router.patch("/{vuln_id}", response_model=StandardResponse)
def review_vuln(vuln_id: str, payload: VulnReview, db: Session = Depends(get_db)):
    v = db.get(Vuln, vuln_id)
    if not v:
        raise HTTPException(404, "漏洞不存在")
    if payload.severity:
        v.severity = payload.severity
    if payload.reviewer_note:
        v.reviewer_note = payload.reviewer_note
    v.status = payload.status
    db.commit()
    return StandardResponse(message="已更新")


@router.delete("/{vuln_id}", response_model=StandardResponse)
def delete_vuln(vuln_id: str, db: Session = Depends(get_db)):
    v = db.get(Vuln, vuln_id)
    if not v:
        raise HTTPException(404, "漏洞不存在")
    db.delete(v)
    db.commit()
    return StandardResponse(message="已删除")
