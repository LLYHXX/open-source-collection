"""MCP 服务器管理路由：添加/启停/测试连接/刷新工具清单。

安全红线：MCP 服务器为第三方程序，默认停用、手动启用；
启用即授权其在本机运行，前端需明示风险。
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..core.mcp_manager import get_mcp_manager
from ..database import get_db
from ..models import MCPServer
from ..schemas import (MCPEnableIn, MCPServerIn, MCPServerOut,
                       StandardResponse)

router = APIRouter(prefix="/mcp", tags=["mcp"],
                   dependencies=[Depends(verify_token)])


def _to_out(s: MCPServer) -> dict:
    """模型 → 响应 dict（args/env 文本反序列化为结构化）。"""
    try:
        args = json.loads(s.args) if s.args else []
    except Exception:  # noqa: BLE001
        args = []
    try:
        env = json.loads(s.env) if s.env else {}
    except Exception:  # noqa: BLE001
        env = {}
    return {
        "id": s.id, "name": s.name, "transport": s.transport,
        "command": s.command, "args": args, "env": env, "url": s.url,
        "enabled": bool(s.enabled), "status": s.status,
        "tool_count": s.tool_count or 0, "last_error": s.last_error or "",
        "created_at": s.created_at,
    }


def _get_or_404(db: Session, server_id: str) -> MCPServer:
    s = db.get(MCPServer, server_id)
    if not s:
        raise HTTPException(404, "MCP 服务器不存在")
    return s


@router.get("/servers", response_model=list[MCPServerOut])
def list_servers(db: Session = Depends(get_db)):
    return [_to_out(s) for s in db.scalars(select(MCPServer))]


@router.post("/servers", response_model=MCPServerOut)
def create_server(payload: MCPServerIn, db: Session = Depends(get_db)):
    name = payload.name.strip()
    command = payload.command.strip()
    if not name or not command:
        raise HTTPException(400, "name 与 command 必填")
    exists = db.scalar(select(MCPServer).where(MCPServer.name == name))
    if exists:
        raise HTTPException(400, f"名称已存在: {name}")
    s = MCPServer(
        name=name, command=command,
        transport=(payload.transport or "stdio").strip() or "stdio",
        args=json.dumps(payload.args or [], ensure_ascii=False),
        env=json.dumps(payload.env or {}, ensure_ascii=False),
        url=payload.url.strip(),
        enabled=False,  # 安全红线：默认停用
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _to_out(s)


@router.put("/servers/{server_id}", response_model=MCPServerOut)
def update_server(server_id: str, payload: MCPServerIn,
                  db: Session = Depends(get_db)):
    s = _get_or_404(db, server_id)
    s.name = payload.name.strip() or s.name
    s.command = payload.command.strip()
    s.transport = (payload.transport or "stdio").strip() or "stdio"
    s.args = json.dumps(payload.args or [], ensure_ascii=False)
    s.env = json.dumps(payload.env or {}, ensure_ascii=False)
    s.url = payload.url.strip()
    s.status = "未连接"
    s.last_error = ""
    db.commit()
    db.refresh(s)
    get_mcp_manager().drop_client(s.id)  # 配置已变，丢弃旧进程与缓存
    return _to_out(s)


@router.delete("/servers/{server_id}", response_model=StandardResponse)
def delete_server(server_id: str, db: Session = Depends(get_db)):
    s = _get_or_404(db, server_id)
    get_mcp_manager().drop_client(s.id)
    db.delete(s)
    db.commit()
    return StandardResponse(message=f"已删除 {s.name}")


@router.post("/servers/{server_id}/test", response_model=StandardResponse)
def test_server(server_id: str, db: Session = Depends(get_db)):
    """测试连接：启动进程握手并列出工具（不要求 enabled）。"""
    s = _get_or_404(db, server_id)
    tools, error = get_mcp_manager().list_tools(s)
    if error:
        s.status = "连接失败"
        s.last_error = error[:2000]
        s.tool_count = 0
        db.commit()
        return StandardResponse(success=False,
                                message=f"连接失败: {error}")
    s.status = "已连接"
    s.last_error = ""
    s.tool_count = len(tools)
    db.commit()
    sample = ", ".join(str(t.get("name")) for t in tools[:8])
    return StandardResponse(
        success=True,
        message=f"连接成功，发现 {len(tools)} 个工具"
                + (f": {sample}" + ("…" if len(tools) > 8 else "") if sample else ""),
        data={"tools": [{"name": t.get("name"),
                         "description": str(t.get("description") or "")[:200]}
                        for t in tools]},
    )


@router.post("/servers/{server_id}/enable", response_model=MCPServerOut)
def enable_server(server_id: str, payload: MCPEnableIn,
                  db: Session = Depends(get_db)):
    """启用/停用。启用时立即验证连接，失败则拒绝启用并写明原因。"""
    s = _get_or_404(db, server_id)
    if payload.enabled:
        tools, error = get_mcp_manager().list_tools(s)
        if error:
            s.enabled = False
            s.status = "连接失败"
            s.last_error = error[:2000]
            db.commit()
            db.refresh(s)
            return _to_out(s)
        s.enabled = True
        s.status = "已连接"
        s.tool_count = len(tools)
        s.last_error = ""
    else:
        s.enabled = False
        s.status = "已停用"
        get_mcp_manager().drop_client(s.id)
    db.commit()
    db.refresh(s)
    return _to_out(s)


@router.post("/refresh", response_model=StandardResponse)
def refresh_all(db: Session = Depends(get_db)):
    """重新连接所有启用服务器并刷新工具清单（状态回写，便于排障）。"""
    mgr = get_mcp_manager()
    servers = db.scalars(select(MCPServer)).all()
    ok, fail = 0, 0
    total_tools = 0
    for s in servers:
        if not s.enabled:
            continue
        tools, error = mgr.list_tools(s)
        if error:
            s.status = "连接失败"
            s.last_error = error[:2000]
            fail += 1
        else:
            s.status = "已连接"
            s.last_error = ""
            s.tool_count = len(tools)
            ok += 1
            total_tools += len(tools)
        db.add(s)
    db.commit()
    return StandardResponse(
        success=fail == 0,
        message=f"刷新完成: {ok} 个服务器在线共 {total_tools} 个工具"
                + (f"，{fail} 个连接失败" if fail else ""),
    )
