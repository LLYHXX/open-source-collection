"""任务路由：创建 / 列表 / 详情 / 启动编排 / 删除。"""
import asyncio
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..core.orchestrator import Orchestrator
from ..database import SessionLocal, get_db
from ..models import Target, Task, Vuln
from ..schemas import StandardResponse, TaskCreate, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(verify_token)])

# 敏感系统目录黑名单（防路径穿越到系统关键路径）
_SENSITIVE_PATH_PARTS = {"etc", "proc", "sys", "dev", "boot", "windows", "system32"}


def _validate_target_url(url: str) -> None:
    """校验目标 URL：必须 http/https，host 不能是内网/私网/链路本地地址。

    防御性校验：攻击探测端本就要请求目标，但不允许用户随意指定内网地址
    作为 target（应通过资产测绘进入），避免 SSRF 打内网。
    """
    if not url or not url.strip():
        raise HTTPException(400, "目标 URL 不能为空")
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            400, f"目标 URL 协议必须为 http/https，当前: {parsed.scheme}"
        )
    host = parsed.hostname or ""
    if not host:
        raise HTTPException(400, "目标 URL 缺少 host")

    # 尝试解析 host 为 IP（可能是 IP 字面量或域名）
    try:
        ip = ipaddress.ip_address(host)
        ips = [ip]
    except ValueError:
        # 域名：DNS 解析
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror as e:
            raise HTTPException(400, f"无法解析域名: {host} ({e})")
        ips = []
        for info in infos:
            addr = info[4][0]
            try:
                ips.append(ipaddress.ip_address(addr))
            except ValueError:
                continue

    for ip in ips:
        if (ip.is_loopback or ip.is_private or ip.is_link_local
                or ip.is_reserved or ip.is_multicast):
            raise HTTPException(
                400,
                f"目标地址 {ip} 属于内网/保留/链路本地地址，"
                f"不允许作为扫描目标（请通过资产测绘收集内网资产）",
            )


def _validate_source_path(source_path: str) -> None:
    """校验白盒源码路径：必须存在，且不能指向系统敏感目录。

    白盒审计需扫描任意用户指定的源码目录，因此只阻断系统敏感目录
    （/etc /proc /sys /dev /boot C:\\Windows 等），不限制在工作区下。
    """
    if not source_path or not source_path.strip():
        raise HTTPException(400, "源码路径不能为空")
    p = Path(source_path).resolve()
    if not p.exists():
        raise HTTPException(400, f"源码路径不存在: {source_path}")
    if not p.is_dir() and not (p.is_file() and p.suffix == ".py"):
        raise HTTPException(400, "源码路径必须是目录或 .py 文件")
    parts_lower = {part.lower() for part in p.parts}
    if parts_lower & _SENSITIVE_PATH_PARTS:
        raise HTTPException(400, "源码路径不能指向系统敏感目录")


@router.post("", response_model=StandardResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return StandardResponse(data={"id": task.id})


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return list(db.scalars(select(Task).order_by(Task.created_at.desc())))


@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    targets = db.scalars(select(Target).where(Target.task_id == task_id)).all()
    vulns = db.scalars(select(Vuln).where(Vuln.task_id == task_id)).all()
    return {
        "task": TaskOut.model_validate(task).model_dump(),
        "targets": len(targets),
        "vulns": len(vulns),
        "pending_vulns": sum(1 for v in vulns if v.status == "ai_reviewed"),
    }


@router.post("/{task_id}/start", response_model=StandardResponse)
async def start_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    if task.status in ("collecting", "running"):
        raise HTTPException(400, f"任务进行中({task.status})，无法重复启动")
    task.status = "collecting"
    db.commit()

    async def _bg():
        db2 = SessionLocal()
        try:
            await Orchestrator(db2).run_task(task_id)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    return StandardResponse(message="任务已启动")


@router.post("/{task_id}/single-site", response_model=StandardResponse)
async def start_single_site(task_id: str, url: str, db: Session = Depends(get_db)):
    """单站浏览器协作（借鉴 AutoHunter 单站协作 + Nanobrowser）。"""
    _validate_target_url(url)
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    async def _bg():
        db2 = SessionLocal()
        try:
            await Orchestrator(db2).run_single_site(task, url)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    return StandardResponse(message=f"已对 {url} 启动浏览器协作")


@router.post("/{task_id}/traffic", response_model=StandardResponse)
async def start_traffic(task_id: str, url: str, db: Session = Depends(get_db)):
    """流量驱动业务逻辑漏洞挖掘闭环（三 Agent 协同）。

    Modeler(AI1 业务建模) → Attacker(AI2 抓包变异攻击多轮自进化)
    → Verifier/Reviewer(AI3 验证初审入库)。
    """
    _validate_target_url(url)
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    async def _bg():
        db2 = SessionLocal()
        try:
            await Orchestrator(db2).run_traffic_pipeline(task, url)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    return StandardResponse(message=f"已对 {url} 启动流量驱动挖掘（三 Agent 闭环）")


@router.post("/{task_id}/whitebox", response_model=StandardResponse)
async def start_whitebox(task_id: str, source_path: str,
                         severity: str = "low",
                         business_context: str = "",
                         db: Session = Depends(get_db)):
    """白盒代码审计流水线（黑白盒模式分离）。

    CodeAuditor(Bandit+Dlint 静态扫源码+LLM 去误报)
    → Reviewer(severity 校准入库)。
    黑盒走 /traffic 或 /run，本接口只扫静态源码。
    """
    _validate_source_path(source_path)
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    async def _bg():
        db2 = SessionLocal()
        try:
            await Orchestrator(db2).run_whitebox_pipeline(
                task, source_path, severity=severity,
                business_context=business_context)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    return StandardResponse(
        message=f"已对 {source_path} 启动白盒代码审计（severity>={severity}）")


@router.post("/{task_id}/multi-agent", response_model=StandardResponse)
async def start_multi_agent(task_id: str, url: str,
                             workflow_name: str = "default_multi_agent",
                             db: Session = Depends(get_db)):
    """多 agent 合作流水线（4 种形态合一）。

    Master 调度 + 并行专精 + Agent 间对话 + 可配置 DAG 编排。
    workflow_name 取值：
      - default_multi_agent：Master 调度 4 专精+Verifier+Reviewer
      - parallel_specialists：4 专精并行 + Reviewer
      - 自定义：在 task.params.workflow 传 DAG JSON
    """
    _validate_target_url(url)
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    async def _bg():
        db2 = SessionLocal()
        try:
            await Orchestrator(db2).run_multi_agent_pipeline(
                task, url, workflow_name=workflow_name)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    return StandardResponse(
        message=f"已对 {url} 启动多 agent 合作（workflow={workflow_name}）")


@router.get("/workflows/preset", response_model=StandardResponse)
def list_preset_workflows():
    """列出预置 workflow 模板（前端拖拽编排用）。"""
    from ..core.workflow_dag import PRESET_WORKFLOWS
    return StandardResponse(
        message=f"共 {len(PRESET_WORKFLOWS)} 个预置 workflow",
        data={"workflows": {k: {"name": v["name"], "description": v["description"]}
                            for k, v in PRESET_WORKFLOWS.items()}},
    )


@router.delete("/{task_id}", response_model=StandardResponse)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    db.delete(task)
    db.commit()
    return StandardResponse(message="已删除")
