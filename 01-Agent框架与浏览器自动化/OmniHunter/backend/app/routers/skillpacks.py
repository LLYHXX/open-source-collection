"""技能包管理路由：安装（GitHub/本地）/启停/删除/列表。

安全红线：技能包为纯提示词+配置，安装时仅做 JSON 校验，
绝不执行包内代码。
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..core import skillpacks
from ..core.skillpacks import SkillPackError
from ..database import get_db
from ..models import SkillPack
from ..schemas import SkillPackEnableIn, SkillPackInstallIn, SkillPackOut, StandardResponse

router = APIRouter(prefix="/skillpacks", tags=["skillpacks"],
                   dependencies=[Depends(verify_token)])


def _to_out(p: SkillPack) -> dict:
    try:
        manifest = json.loads(p.manifest or "{}")
    except Exception:  # noqa: BLE001
        manifest = {}
    return {
        "id": p.id, "name": p.name, "version": p.version,
        "description": p.description, "source": p.source,
        "enabled": bool(p.enabled), "manifest": manifest,
        "installed_at": p.installed_at,
    }


def _upsert(db: Session, manifest: dict, path, source: str) -> SkillPack:
    name = manifest["name"]
    existing = db.scalar(select(SkillPack).where(SkillPack.name == name))
    if existing:
        existing.version = str(manifest.get("version", "1.0.0"))
        existing.description = str(manifest.get("description", ""))
        existing.source = source
        existing.path = str(path)
        existing.manifest = json.dumps(manifest, ensure_ascii=False)
        db.commit()
        db.refresh(existing)
        return existing
    p = SkillPack(
        name=name,
        version=str(manifest.get("version", "1.0.0")),
        description=str(manifest.get("description", "")),
        source=source, path=str(path),
        manifest=json.dumps(manifest, ensure_ascii=False),
        enabled=False,  # 默认停用，手动启用
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("", response_model=list[SkillPackOut])
def list_packs(db: Session = Depends(get_db)):
    return [_to_out(p) for p in db.scalars(select(SkillPack))]


@router.post("/install", response_model=SkillPackOut)
def install(payload: SkillPackInstallIn, db: Session = Depends(get_db)):
    git_url = (payload.git_url or "").strip()
    local_path = (payload.local_path or "").strip()
    if bool(git_url) == bool(local_path):
        raise HTTPException(400, "git_url 与 local_path 必须二选一")
    try:
        if git_url:
            manifest, path = skillpacks.install_from_git(git_url)
            source = git_url
        else:
            manifest, path = skillpacks.install_from_local(local_path)
            source = local_path
    except SkillPackError as e:
        raise HTTPException(400, str(e))
    p = _upsert(db, manifest, path, source)
    return _to_out(p)


@router.post("/{pack_id}/enable", response_model=SkillPackOut)
def enable_pack(pack_id: str, payload: SkillPackEnableIn,
                db: Session = Depends(get_db)):
    p = db.get(SkillPack, pack_id)
    if not p:
        raise HTTPException(404, "技能包不存在")
    p.enabled = bool(payload.enabled)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.delete("/{pack_id}", response_model=StandardResponse)
def delete_pack(pack_id: str, db: Session = Depends(get_db)):
    p = db.get(SkillPack, pack_id)
    if not p:
        raise HTTPException(404, "技能包不存在")
    # 仅删除安装副本（data/skillpacks/<name>），不触碰来源目录
    if p.path:
        import shutil
        from pathlib import Path

        dst = Path(p.path).resolve()
        guard = skillpacks.SKILLPACKS_DIR.resolve()
        if guard in dst.parents and dst.is_dir():
            shutil.rmtree(dst, ignore_errors=True)
    db.delete(p)
    db.commit()
    return StandardResponse(message=f"已卸载 {p.name}")
