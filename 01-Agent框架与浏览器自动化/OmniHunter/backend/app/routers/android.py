"""移动靶场路由：安卓模拟器（AVD）管理 + APP 安装 + 抓包联动。

用于 APP / 小程序类目标的漏洞挖掘：模拟器挂 mitmproxy 代理录制流量，
流量回灌攻击探测流水线（复用 AI2 的 traffic_tool）。
"""
import asyncio
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..schemas import (AndroidAppLaunch, AndroidAvdCreate, AndroidAvdStart,
                       AndroidImageInstall, StandardResponse)
from ..tools import android_emulator as emu

router = APIRouter(prefix="/android", tags=["android"],
                   dependencies=[Depends(verify_token)])


@router.get("/status", response_model=StandardResponse)
def android_status():
    """环境自检：SDK/JDK/工具链/镜像/AVD 概况（无 SDK 时优雅降级，可直接引导安装）。"""
    return StandardResponse(success=True, message="ok", data=emu.detect_environment())


@router.post("/bootstrap", response_model=StandardResponse)
def android_bootstrap(include_emulator: bool = True):
    """一键引导：自动下载 JDK17 + cmdline-tools + platform-tools + emulator（后台任务）。"""
    jid = emu.bootstrap_async(include_emulator=include_emulator)
    return StandardResponse(success=True, message="引导任务已启动",
                            data={"job_id": jid})


@router.get("/jobs/{job_id}", response_model=StandardResponse)
def android_job(job_id: str):
    job = emu.job_get(job_id)
    if not job:
        return StandardResponse(success=False, message="任务不存在或已过期")
    return StandardResponse(success=True, message=job["status"],
                            data=job)


@router.post("/images/install", response_model=StandardResponse)
def android_install_image(payload: AndroidImageInstall):
    """安装系统镜像（后台任务，体积约 1.3~1.8GB）。"""
    jid = emu.install_image_async(payload.pkg)
    return StandardResponse(success=True, message="镜像安装任务已启动",
                            data={"job_id": jid})


@router.get("/avds", response_model=StandardResponse)
def android_avds():
    return StandardResponse(success=True, message="ok",
                            data={"avds": emu.list_avds()})


@router.post("/avds", response_model=StandardResponse)
def android_create_avd(payload: AndroidAvdCreate):
    """创建 AVD（可自定义内存/核心/分辨率/密度）。"""
    info = emu.create_avd(payload.name, payload.image,
                          memory_mb=payload.memory_mb, cores=payload.cores,
                          width=payload.width, height=payload.height,
                          density=payload.density)
    return StandardResponse(success=True, message=f"AVD {payload.name} 创建成功",
                            data=info)


@router.delete("/avds/{name}", response_model=StandardResponse)
def android_delete_avd(name: str):
    return StandardResponse(success=True, message=f"已删除 {name}",
                            data=emu.delete_avd(name))


@router.post("/avds/{name}/start", response_model=StandardResponse)
def android_start_avd(name: str, payload: AndroidAvdStart):
    """启动 AVD；proxy=true 时自动挂 mitmproxy 抓包代理并装系统 CA 证书。"""
    info = emu.start_avd(name, headless=payload.headless,
                         proxy_port=payload.proxy_port if payload.proxy else 0,
                         memory_mb=payload.memory_mb or None,
                         cores=payload.cores or None,
                         install_cert=payload.install_cert)
    return StandardResponse(success=True, message=f"AVD {name} 启动中",
                            data=info)


@router.post("/avds/{name}/stop", response_model=StandardResponse)
def android_stop_avd(name: str):
    return StandardResponse(success=True, message=f"已停止 {name}",
                            data=emu.stop_avd(name))


@router.get("/devices", response_model=StandardResponse)
def android_devices():
    return StandardResponse(success=True, message="ok",
                            data={"devices": emu.adb_devices()})


@router.post("/apps/install", response_model=StandardResponse)
async def android_install_apk(file: UploadFile = File(...), serial: str = Form(...)):
    """上传 APK 安装到指定模拟器（临时文件用完即删）。"""
    if Path(file.filename or "app.apk").suffix.lower() != ".apk":
        return StandardResponse(success=False, message="仅支持 .apk 文件")
    # uuid 命名防并发同秒碰撞（时间戳命名会互相覆盖导致安装损坏）
    tmp = Path(tempfile.gettempdir()) / f"oh_apk_{uuid.uuid4().hex}.apk"
    try:
        with open(tmp, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
        # 同步 adb 安装（最长 600s）移入线程执行，避免阻塞事件循环
        info = await asyncio.to_thread(emu.install_apk, serial, str(tmp))
        return StandardResponse(success=True, message=f"APK 已安装到 {serial}",
                                data=info)
    finally:
        tmp.unlink(missing_ok=True)  # create-delete 配对，防磁盘泄漏


@router.post("/apps/launch", response_model=StandardResponse)
def android_launch_app(payload: AndroidAppLaunch):
    return StandardResponse(success=True, message="已启动",
                            data=emu.launch_app(payload.serial, payload.package,
                                                payload.activity or ""))


@router.post("/apps/uninstall", response_model=StandardResponse)
def android_uninstall_app(payload: AndroidAppLaunch):
    return StandardResponse(success=True, message="已卸载",
                            data=emu.uninstall_app(payload.serial, payload.package))


@router.get("/apps/list", response_model=StandardResponse)
def android_list_apps(serial: str, third_party: bool = True):
    return StandardResponse(success=True, message="ok",
                            data={"packages": emu.list_packages(serial, third_party)})


@router.post("/traffic/start", response_model=StandardResponse)
def android_traffic_start(port: int = 8082, duration: int = 3600):
    """开启 mitmproxy 流量录制（配合模拟器代理使用，复用攻击探测端捕获通道）。"""
    from ..tools.traffic_tool import start_traffic_capture

    msg = start_traffic_capture(proxy_port=port, duration=duration)
    return StandardResponse(success=True, message=msg)


@router.post("/traffic/stop", response_model=StandardResponse)
def android_traffic_stop():
    from ..tools.traffic_tool import stop_traffic_capture

    msg = stop_traffic_capture()
    return StandardResponse(success=True, message=msg)


@router.get("/traffic", response_model=StandardResponse)
def android_traffic(filter: str = "", max_items: int = 50):
    from ..tools.traffic_tool import get_captured_traffic

    return StandardResponse(success=True, message="ok",
                            data={"traffic": get_captured_traffic(
                                filter=filter, max_items=max_items)})
