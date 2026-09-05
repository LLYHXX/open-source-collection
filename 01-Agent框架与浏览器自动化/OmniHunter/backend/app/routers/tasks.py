"""任务路由：创建 / 列表 / 详情 / 启动编排 / 删除。"""
import asyncio
import ipaddress
import logging
import socket
from pathlib import Path
from urllib.parse import urlparse

log = logging.getLogger("aififteen-hunter.tasks")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..core.orchestrator import Orchestrator
from ..database import SessionLocal, get_db
from ..models import TASK_PENDING_APPROVAL, TASK_REJECTED, Target, Task, Vuln
from ..schemas import StandardResponse, TaskCreate, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(verify_token)])

# 敏感系统目录黑名单（防路径穿越到系统关键路径）
_SENSITIVE_PATH_PARTS = {"etc", "proc", "sys", "dev", "boot", "windows", "system32"}


def _set_task_failed(task_id: str, err: Exception) -> None:
    """后台任务异常时独立开一个 DB Session，把 task.status 写回 failed。
    不依赖调用方的 db2（可能已经被异常置为 rollback-only 或过期），
    避免"启动后抛异常 → 任务永远卡在 collecting/running"。
    """
    from ..models import Task
    dbx = SessionLocal()
    try:
        t = dbx.get(Task, task_id)
        if t is not None:
            t.status = "failed"
            t.error = f"[{type(err).__name__}] {err}"[:2000]
            try:
                dbx.commit()
            except Exception:  # noqa: BLE001 —— SQLite 锁冲突时尽最大努力即可
                dbx.rollback()
    finally:
        dbx.close()


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
    data = payload.model_dump()
    # status 白名单：避免用户直接写 collecting/running/done 绕过状态机
    allowed_status = {None, "", "pending", TASK_PENDING_APPROVAL, TASK_REJECTED}
    s = data.get("status")
    if s not in allowed_status:
        raise HTTPException(400, f"非法 status: {s}")
    if not s:
        data["status"] = "pending"
    task = Task(**data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return StandardResponse(data={"id": task.id, "status": task.status})


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    try:
        return list(db.scalars(select(Task).order_by(Task.created_at.desc())))
    except Exception as e:  # noqa: BLE001
        # 兜底：缺列迁移未完成（如 tasks.error 列未加上）时，
        # 手动按列查再组装 dict 走 Pydantic 校验，避免整体 500 → 前端表现"任务全部消失"。
        msg = str(e).lower()
        if "no such column" in msg:
            log.warning("[tasks.list] 缺列，回退兼容加载: %s", e)
            rows = db.execute(
                select(Task.id, Task.name, Task.mode, Task.status,
                       Task.source, Task.collect_method,
                       Task.collect_query, Task.created_at)
                .order_by(Task.created_at.desc())
            ).all()
            return [
                TaskOut.model_validate({
                    "id": r[0], "name": r[1], "mode": r[2], "status": r[3],
                    "source": r[4], "collect_method": r[5],
                    "collect_query": r[6] or "", "created_at": r[7],
                    "error": "",  # 缺列时给默认值
                })
                for r in rows
            ]
        # 其他错误继续上抛
        raise


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
    task.error = ""
    db.commit()

    async def _bg():
        db2 = SessionLocal()
        try:
            await Orchestrator(db2).run_task(task_id)
        except Exception as e:  # noqa: BLE001
            _set_task_failed(task_id, e)
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
        except Exception as e:  # noqa: BLE001
            _set_task_failed(task_id, e)
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
        except Exception as e:  # noqa: BLE001
            _set_task_failed(task_id, e)
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
        except Exception as e:  # noqa: BLE001
            _set_task_failed(task_id, e)
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
        except Exception as e:  # noqa: BLE001
            _set_task_failed(task_id, e)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    return StandardResponse(
        message=f"已对 {url} 启动多 agent 合作（workflow={workflow_name}）")


@router.post("/{task_id}/engine-scan", response_model=StandardResponse)
async def start_engine_scan(task_id: str, url: str,
                            admin_cookie: str = "",
                            user_cookie: str = "",
                            db: Session = Depends(get_db)):
    """自研检测引擎流水线：指纹前置 → 确定性插件检测 → 独立复现
    → CVSS 自动定级 → 入库。

    admin_cookie/user_cookie 可选，提供后启用三身份越权遍历
    （auth_traverse 确定性检测）。task.mode="engine" 时
    /tasks/{id}/start 与定时任务也走同一条引擎流水线。
    """
    _validate_target_url(url)
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    async def _bg():
        db2 = SessionLocal()
        try:
            orch = Orchestrator(db2)
            await orch.run_engine_pipeline(
                task, url,
                admin_cookie=admin_cookie, user_cookie=user_cookie)
        except Exception as e:  # noqa: BLE001
            _set_task_failed(task_id, e)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    return StandardResponse(message=f"已对 {url} 启动自研引擎扫描")


@router.post("/{task_id}/collab", response_model=StandardResponse)
async def start_collab(task_id: str, url: str,
                        admin_cookie: str = "",
                        user_cookie: str = "",
                        user2_cookie: str = "",
                        anon_probe: bool = True,
                        enable_attacker: bool = True,
                        db: Session = Depends(get_db)):
    """单站协作流水线：权限发现专项 + LLM 攻击 Agent 协同。

    用户需求：「单站深挖 — 都有什么权限？让 agent 自己自动挖掘」

    流水线：
      SiteProfiler 单站资产收集 → Modeler 业务建模
      → PermissionAgent 权限发现专项（5 类权限检测 + 权限矩阵）
      → Attacker（可选，基于权限矩阵做变异攻击）
      → Verifier 独立复现 + Reviewer 极理性初审 → 入库

    身份会话（admin_cookie/user_cookie/user2_cookie）由前端提供，
    至少需要 user_cookie 才能跑权限矩阵；admin_cookie 用于垂直越权检测；
    user2_cookie 用于水平越权检测；anon_probe=True 测未授权访问。
    """
    _validate_target_url(url)
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    async def _bg():
        db2 = SessionLocal()
        try:
            orch = Orchestrator(db2)
            await orch.run_collab_pipeline(
                task, url,
                admin_cookie=admin_cookie, user_cookie=user_cookie,
                user2_cookie=user2_cookie, anon_probe=anon_probe,
                enable_attacker=enable_attacker,
            )
        except Exception as e:  # noqa: BLE001
            _set_task_failed(task_id, e)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    id_count = sum(1 for c in (admin_cookie, user_cookie, user2_cookie) if c)
    return StandardResponse(
        message=f"已对 {url} 启动单站协作（{id_count} 个身份会话，"
                f"anon_probe={anon_probe}, attacker={enable_attacker}）")


@router.post("/engine-scan-url", response_model=StandardResponse)
async def engine_scan_url(url: str,
                          admin_cookie: str = "",
                          user_cookie: str = "",
                          db: Session = Depends(get_db)):
    """免建任务直接引擎扫描单 URL（控制台/第三方便捷入口）。

    后台执行，结果与其他漏洞一样入库，在「漏洞」页复审。
    """
    _validate_target_url(url)

    async def _bg():
        db2 = SessionLocal()
        quick_task = None
        try:
            orch = Orchestrator(db2)
            from ..models import Task
            quick_task = Task(
                name=f"快速引擎扫描 {url[:60]}", mode="engine",
                source="manual", manual_targets=url, status="running",
            )
            db2.add(quick_task)
            db2.commit()
            await orch.run_engine_pipeline(
                quick_task, url,
                admin_cookie=admin_cookie, user_cookie=user_cookie)
        except Exception as e:  # noqa: BLE001 —— 快速任务失败也要写回 failed + error
            if quick_task is not None and quick_task.id:
                _set_task_failed(quick_task.id, e)
        finally:
            db2.close()

    asyncio.create_task(_bg())
    return StandardResponse(message=f"已对 {url} 启动引擎扫描（免建任务，结果见漏洞页）")


@router.get("/engine/detectors", response_model=StandardResponse)
def list_engine_detectors():
    """列出引擎检测插件清单（id/类型/是否无副作用）。"""
    from ..engine import ScanEngine
    return StandardResponse(
        message="ok",
        data={"detectors": ScanEngine().list_detectors()},
    )


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


# ===== Miner 审批流：pending_approval → pending / rejected =====


@router.post("/{task_id}/approve", response_model=StandardResponse)
async def approve_task(task_id: str, db: Session = Depends(get_db)):
    """Miner 自动生成的 pending_approval 任务 → 用户批准后立即走编排。"""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    if task.status != TASK_PENDING_APPROVAL:
        raise HTTPException(
            400,
            f"仅状态 {TASK_PENDING_APPROVAL} 可审批，当前: {task.status}",
        )
    task.status = "pending"
    db.commit()

    # 立即启动（复用 start_task 的 Orchestrator.run_task 后台模式，统一安全包装）
    from ..core.bgtasks import safe_create_task

    async def _bg():
        db2 = SessionLocal()
        try:
            await Orchestrator(db2).run_task(task_id)
        except Exception as e:  # noqa: BLE001
            _set_task_failed(task_id, e)
        finally:
            db2.close()

    safe_create_task(_bg(), name=f"task:approve:{task_id}",
                     on_error=lambda e: _set_task_failed(task_id, e))
    return StandardResponse(message="已批准并启动任务")


@router.post("/{task_id}/reject", response_model=StandardResponse)
def reject_task(task_id: str, db: Session = Depends(get_db)):
    """Miner 自动生成的 pending_approval 任务 → 拒绝后不再可启动。"""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    if task.status != TASK_PENDING_APPROVAL:
        raise HTTPException(
            400,
            f"仅状态 {TASK_PENDING_APPROVAL} 可拒绝，当前: {task.status}",
        )
    task.status = TASK_REJECTED
    db.commit()
    return StandardResponse(message="已拒绝")
