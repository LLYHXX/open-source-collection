"""MCP stdio 客户端：同步 JSON-RPC 2.0（换行分隔帧，MCP stdio 传输标准）。

借鉴模型上下文协议（Model Context Protocol）规范实现最小客户端：
initialize 握手 → tools/list 发现 → tools/call 调用。
同步 subprocess 实现与代码库现有工具（mitan/sqlmap 等同步调用）保持一致。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import threading


class MCPError(Exception):
    """MCP 通信错误（连接/协议/超时）。"""


class MCPStdioClient:
    """一个 MCP server 进程对应一个客户端实例；线程安全（内部锁串行化）。"""

    PROTOCOL_VERSION = "2024-11-05"
    CLIENT_INFO = {"name": "aififteen-hunter", "version": "1.0.0"}

    def __init__(self, command: str, args: list | None = None,
                 env: dict | None = None, startup_timeout: float = 20.0):
        self._command = command
        self._args = list(args or [])
        self._env = dict(env or {})
        self._startup_timeout = startup_timeout
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._next_id = 0
        self._server_info: dict = {}

    # ---- 进程管理 ----
    def _resolve_command(self) -> str:
        exe = shutil.which(self._command)
        if not exe and self._command.lower().endswith(".cmd"):
            exe = self._command
        if not exe:
            raise MCPError(f"找不到可执行文件: {self._command}（npx/uvx 需已安装 Node/uv）")
        return exe

    def _spawn(self) -> None:
        exe = self._resolve_command()
        env = None
        if self._env:
            import os
            env = {**os.environ, **{str(k): str(v) for k, v in self._env.items()}}
        try:
            self._proc = subprocess.Popen(
                [exe, *self._args],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True, encoding="utf-8", errors="replace",
                env=env, cwd=None, shell=False,
            )
        except Exception as e:  # noqa: BLE001
            raise MCPError(f"启动 MCP 进程失败: {e}") from e

    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def close(self) -> None:
        proc, self._proc = self._proc, None
        if proc is None:
            return
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:  # noqa: BLE001
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass

    # ---- 帧收发 ----
    def _send(self, payload: dict) -> None:
        if not self.alive():
            raise MCPError("MCP 进程未运行")
        line = json.dumps(payload, ensure_ascii=False)
        try:
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()
        except Exception as e:  # noqa: BLE001
            raise MCPError(f"写入 MCP stdin 失败: {e}") from e

    def _recv(self, want_id: int, timeout: float) -> dict:
        """读行直到拿到 id 匹配的响应（跳过通知/请求）。"""
        import time
        deadline = time.monotonic() + timeout
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise MCPError(f"等待 MCP 响应超时({timeout}s)")
            line = self._proc.stdout.readline()
            if line == "":  # EOF
                raise MCPError("MCP 进程已退出（stdout 关闭）")
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue  # 忽略非 JSON 噪声行
            if not isinstance(msg, dict):
                continue
            if msg.get("id") == want_id and ("result" in msg or "error" in msg):
                return msg

    def _request(self, method: str, params: dict | None, timeout: float) -> dict:
        self._next_id += 1
        rid = self._next_id
        payload: dict = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)
        msg = self._recv(rid, timeout)
        if "error" in msg:
            err = msg["error"] or {}
            raise MCPError(f"MCP 错误[{method}]: {err.get('message', err)}")
        return msg.get("result") or {}

    # ---- 协议三步 ----
    def initialize(self) -> dict:
        """幂等握手：未启动则启动进程，完成 initialize + initialized 通知。"""
        with self._lock:
            if not self.alive():
                self.close()
                self._spawn()
                result = self._request(
                    "initialize",
                    {"protocolVersion": self.PROTOCOL_VERSION,
                     "capabilities": {}, "clientInfo": self.CLIENT_INFO},
                    self._startup_timeout,
                )
                self._server_info = result or {}
                # 通知：无 id，无需等响应
                self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            return self._server_info

    def list_tools(self, timeout: float = 15.0) -> list[dict]:
        """返回 tools 列表：[{name, description, inputSchema}]。"""
        self.initialize()
        with self._lock:
            result = self._request("tools/list", {}, timeout)
            tools = result.get("tools") or []
            return [t for t in tools if isinstance(t, dict) and t.get("name")]

    def call_tool(self, name: str, arguments: dict | None = None,
                  timeout: float = 60.0) -> str:
        """调用工具，返回文本结果（content[].text 拼接；isError 时文本以 [MCP错误] 开头）。"""
        self.initialize()
        with self._lock:
            result = self._request(
                "tools/call",
                {"name": name, "arguments": arguments or {}},
                timeout,
            )
        texts: list[str] = []
        for item in (result.get("content") or []):
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(str(item.get("text", "")))
        out = "\n".join(texts).strip()
        if result.get("isError"):
            return f"[MCP错误] {out or '工具执行失败'}"
        return out or "（MCP 工具无文本输出）"
