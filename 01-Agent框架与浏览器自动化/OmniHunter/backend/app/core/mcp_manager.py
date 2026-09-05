"""MCP 服务器管理器：进程生命周期 + 工具缓存 + 注入 ToolRegistry。

- 客户端按 server_id 懒启动，崩溃自动重启一次；
- 每服务器请求串行化（MVP 足够）；
- load_into_registry：把启用服务器的全部工具注册为 mcp__{server}__{tool}，
  失败服务器注册占位工具返回友好提示（对齐"不崩溃"风格）。
"""
from __future__ import annotations

import json
import re
import threading

from .mcp_client import MCPError, MCPStdioClient

_SANITIZE = re.compile(r"[^a-zA-Z0-9_]+")
_PLACEHOLDER_LIMIT = 64


def _sanitize(name: str) -> str:
    return _SANITIZE.sub("_", str(name).strip().lower()).strip("_") or "tool"


def _safe_json_loads(text: str, default):
    try:
        v = json.loads(text) if text else default
        return v if isinstance(v, type(default)) else default
    except Exception:  # noqa: BLE001
        return default


class MCPManager:
    def __init__(self):
        self._clients: dict[str, MCPStdioClient] = {}
        self._tools_cache: dict[str, list[dict]] = {}
        self._config_fingerprint: dict[str, str] = {}  # 配置变更检测
        self._global_lock = threading.Lock()

    # ---- 客户端生命周期 ----
    def _fp(self, server) -> str:
        return json.dumps([server.command, server.args, server.env, server.url],
                          ensure_ascii=False, sort_keys=True)

    def get_client(self, server) -> MCPStdioClient:
        """server 为 MCPServer 模型实例；配置变更时自动重建客户端。"""
        with self._global_lock:
            fp = self._fp(server)
            client = self._clients.get(server.id)
            if client is not None and self._config_fingerprint.get(server.id) != fp:
                client.close()
                client = None
            if client is None:
                client = MCPStdioClient(
                    command=server.command,
                    args=_safe_json_loads(server.args, []),
                    env=_safe_json_loads(server.env, {}),
                )
                self._clients[server.id] = client
                self._config_fingerprint[server.id] = fp
                self._tools_cache.pop(server.id, None)
            return client

    def drop_client(self, server_id: str) -> None:
        with self._global_lock:
            client = self._clients.pop(server_id, None)
            if client:
                client.close()
            self._tools_cache.pop(server_id, None)
            self._config_fingerprint.pop(server_id, None)

    def shutdown_all(self) -> None:
        with self._global_lock:
            for client in self._clients.values():
                try:
                    client.close()
                except Exception:  # noqa: BLE001
                    pass
            self._clients.clear()
            self._tools_cache.clear()
            self._config_fingerprint.clear()

    # ---- 工具发现 ----
    def list_tools(self, server) -> tuple[list[dict], str]:
        """返回 (tools, error)。成功 error 为空。"""
        try:
            client = self.get_client(server)
            tools = client.list_tools()
            self._tools_cache[server.id] = tools
            return tools, ""
        except MCPError as e:
            return [], str(e)
        except Exception as e:  # noqa: BLE001
            return [], f"{type(e).__name__}: {e}"

    # ---- 注册注入 ----
    def load_into_registry(self, reg, db) -> int:
        """把所有 enabled 服务器的工具注入 reg；返回注册的工具数。

        db 为 SQLAlchemy Session（由调用方管理生命周期）。
        """
        from ..models import MCPServer

        registered = 0
        servers = db.query(MCPServer).filter(MCPServer.enabled.is_(True)).all()
        for server in servers:
            tools, error = self.list_tools(server)
            if error:
                server.status = "连接失败"
                server.last_error = error[:2000]
                server.tool_count = 0
                db.add(server)
                reg.register(
                    f"mcp__{_sanitize(server.name)}__unavailable",
                    lambda sn=server.name, er=error: (
                        f"MCP 服务器 {sn} 当前不可用: {er}。"
                        "请在设置页检查命令/参数，或测试连接。"
                    ),
                    f"[MCP:{server.name}] 服务器不可用（连接失败占位工具）",
                    {"type": "object", "properties": {}},
                )
                continue

            server.status = "已连接"
            server.last_error = ""
            server.tool_count = len(tools)
            db.add(server)
            for tool in tools:
                raw_name = str(tool.get("name", "")).strip()
                if not raw_name:
                    continue
                reg_name = f"mcp__{_sanitize(server.name)}__{_sanitize(raw_name)}"
                description = str(tool.get("description") or raw_name).strip()
                schema = tool.get("inputSchema")
                if not isinstance(schema, dict) or schema.get("type") != "object":
                    schema = {"type": "object", "properties": {}}
                reg.register(
                    reg_name,
                    self._make_caller(server, raw_name),
                    f"[MCP:{server.name}] {description}"[:_PLACEHOLDER_LIMIT * 4],
                    schema,
                )
                registered += 1
        try:
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        return registered

    def _make_caller(self, server, tool_name: str):
        """闭包：通过客户端调用远端工具；错误返回文本而非抛异常。"""

        def _call(**kwargs):
            try:
                client = self.get_client(server)
                return client.call_tool(tool_name, kwargs)
            except MCPError as e:
                return f"[MCP错误] {e}"
            except Exception as e:  # noqa: BLE001
                return f"[MCP错误] {type(e).__name__}: {e}"

        return _call


_manager: MCPManager | None = None
_manager_lock = threading.Lock()


def get_mcp_manager() -> MCPManager:
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = MCPManager()
        return _manager
