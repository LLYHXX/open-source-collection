"""动态设置路由：存库，优先级高于 .env（借鉴 AutoHunter 设置页）。"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import Setting
from ..schemas import SettingOut, StandardResponse, SettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"],
                   dependencies=[Depends(verify_token)])


@router.get("", response_model=list[SettingOut])
def list_settings(db: Session = Depends(get_db)):
    return list(db.scalars(select(Setting)))


@router.put("", response_model=StandardResponse)
def update_setting(payload: SettingUpdate, db: Session = Depends(get_db)):
    s = db.get(Setting, payload.key)
    if not s:
        s = Setting(key=payload.key, value=payload.value)
        db.add(s)
    else:
        s.value = payload.value
    db.commit()
    return StandardResponse(message="已保存")
