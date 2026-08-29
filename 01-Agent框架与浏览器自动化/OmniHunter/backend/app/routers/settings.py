"""动态设置路由：存库，优先级高于 .env（借鉴 AutoHunter 设置页）。

保存后立即应用覆盖到运行中的 settings 实例，无需重启。
提供资产测绘平台（FOFA/Quake/Hunter/ZoomEye/Shodan/Censys）连通性测试端点。
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..config import apply_dynamic_overrides
from ..database import get_db
from ..models import Setting
from ..schemas import (AssetPlatformTestIn, StandardResponse, SettingOut,
                       SettingUpdate)
from ..tools import asset_platforms

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
    # 即时生效：覆盖到当前 settings 实例（键不区分大小写）
    applied = apply_dynamic_overrides({payload.key: payload.value})
    msg = "已保存并即时生效" if applied else "已保存（键不匹配后端配置项，仅存库）"
    return StandardResponse(message=msg)


@router.post("/asset-platforms/test", response_model=StandardResponse)
def test_asset_platform(payload: AssetPlatformTestIn,
                        db: Session = Depends(get_db)):
    """资产测绘平台连通性测试：用默认或自定义查询语句实际调用平台 API。"""
    from ..config import get_settings

    settings = get_settings()
    # 先平台白名单（避免任意 platform 拼接 settings 属性名探测配置状态）
    if payload.platform not in asset_platforms.DEFAULT_TEST_QUERY:
        return StandardResponse(success=False,
                                message=f"未知平台: {payload.platform}")
    query = (payload.query or "").strip() or \
        asset_platforms.DEFAULT_TEST_QUERY.get(payload.platform, "")
    if not query:
        return StandardResponse(success=False, message="缺少查询语句")
    if not getattr(settings, f"{payload.platform}_key", ""):
        return StandardResponse(success=False,
                                message=f"未配置 {payload.platform.upper()}_KEY")
    items, err = asset_platforms.search_platform(payload.platform, query,
                                                 settings, max_results=5)
    if err:
        return StandardResponse(success=False, message=err)
    sample = ", ".join(i.get("host", "") for i in items[:3])
    return StandardResponse(
        success=True,
        message=f"连通正常，查询到 {len(items)} 条"
                + (f"，示例: {sample}" if sample else ""),
        data={"items": items},
    )
