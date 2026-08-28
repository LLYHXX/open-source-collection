"""流量监听工具（AI2 攻击探测端核心）：mitmproxy 录制 + flow 读取。

轻量 MVP：mitmproxy 纯 Python，已通过 backend/sitecustomize.py 把 vendor 注入
sys.path；启动时用 `python -c "from mitmproxy.tools.main import mitmdump; mitmdump()"`
子进程录制 flows 到临时文件，读取用 mitmproxy.io.FlowReader。

封装「开启流量监听」「获取捕获流量」「停止监听」三个工具函数给 AI2 调用。
单实例 + lock，避免多会话并发冲突（后续可扩展会话隔离）。
"""
import os
import subprocess
import sys
import tempfile
import threading
import time

from . import which


# 单实例锁与会话状态（MVP：全局单会话）
_lock = threading.Lock()
_session: dict = {
    "process": None,     # mitmdump 子进程
    "flow_file": "",     # 录制文件路径
    "proxy_port": 0,
    "started_at": 0.0,
    "duration": 0,
}


def _find_mitmdump_cmd() -> list[str] | None:
    """构造 mitmdump 启动命令。

    优先级：
      1) PATH 中的 mitmdump exe（which 探测）
      2) vendor/bin 或 vendor/Scripts 下的 mitmdump 脚本
      3) `python -c` 调用 mitmproxy.tools.main:mitmdump（纯 python 兜底）
    """
    exe = which("mitmdump")
    if exe:
        return [exe]
    # vendor/bin 下查找（Windows: .exe，Linux: 无后缀）
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(here))
    for bin_dir in (os.path.join(backend_dir, "vendor", "bin"),
                    os.path.join(backend_dir, "vendor", "Scripts")):
        for name in ("mitmdump.exe", "mitmdump", "mitmdump-script.py"):
            p = os.path.join(bin_dir, name)
            if os.path.exists(p):
                return [p]
    # 用当前 python 解释器 + mitmproxy Python API（mitmproxy 已注入 sys.path）
    if sys.executable:
        return [sys.executable, "-c",
                "from mitmproxy.tools.main import mitmdump; mitmdump()"]
    return None


def start_traffic_capture(proxy_port: int = 8082, duration: int = 60) -> str:
    """开启 mitmproxy 流量监听，录制 flows 到临时文件。

    duration 秒后建议主动 stop_traffic_capture；本函数返回启动状态。
    请将浏览器/客户端 HTTP/HTTPS 代理指向 127.0.0.1:proxy_port。
    """
    with _lock:
        proc = _session.get("process")
        if proc is not None and proc.poll() is None:
            return (f"已有监听进行中（端口 {_session['proxy_port']}），"
                    f"flow 文件: {_session['flow_file']}")

        # 清理上一轮遗留的 flow 文件（上次未正常 stop 时的残留）
        old_flow = _session.get("flow_file", "")
        if old_flow:
            try:
                os.unlink(old_flow)
            except Exception:  # noqa: BLE001 文件可能已被删
                pass

        cmd = _find_mitmdump_cmd()
        if not cmd:
            return ("mitmproxy 未安装或未注入 sys.path。"
                    "安装: python -m pip install --target=vendor mitmproxy，"
                    "并确认 backend/sitecustomize.py 已把 vendor 加入 sys.path。")

        flow_file = tempfile.NamedTemporaryFile(
            suffix=".flow", delete=False, prefix="omnihunter_traffic_"
        ).name

        # console_script 调用约定：mitmdump() 内部用 argparse 解析 sys.argv[1:]，
        # 所以这里只传参数本身，不要再加 "mitmdump" 程序名前缀（否则报错
        # "unrecognized arguments: mitmdump"）
        full_cmd = cmd + ["-p", str(proxy_port),
                          "-w", flow_file, "--quiet",
                          "--set", "ssl_insecure=true"]
        try:
            # stderr 用 DEVNULL：mitmdump 长跑 stderr 持续输出，
            # 用 PIPE 不读取会塞满缓冲区导致子进程阻塞死锁
            proc = subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        except Exception as e:  # noqa: BLE001
            return f"启动 mitmdump 失败: {e}"

        # 短暂检查：若端口被占用/mitmproxy 启动失败，进程会立即退出
        time.sleep(0.8)
        if proc.poll() is not None:
            return (f"mitmdump 启动后立即退出（端口 {proxy_port} 可能被占用，"
                    f"或 mitmproxy CA 证书未安装）。flow 文件: {flow_file}")

        _session.update(process=proc, flow_file=flow_file, proxy_port=proxy_port,
                        started_at=time.time(), duration=duration)
        return (f"已开启流量监听 端口 {proxy_port}，录制到 {flow_file}。"
                f"请把浏览器/客户端 HTTP/HTTPS 代理指向 127.0.0.1:{proxy_port}。"
                f"建议 {duration}s 后调 stop_traffic_capture 停止并读取流量。")


def get_captured_traffic(filter: str = "", max_items: int = 50) -> str:
    """读取已录制的流量，返回 method+url+status+关键 headers+body 片段摘要。

    可在监听进行中或停止后调用；录制中读取可能因文件未刷盘而丢尾部，
    建议先 stop_traffic_capture 再读全量。
    """
    with _lock:
        flow_file = _session.get("flow_file", "")
        if not flow_file or not os.path.exists(flow_file):
            return "无录制文件。请先 start_traffic_capture。"

    try:
        from mitmproxy.io import FlowReader  # type: ignore
        from mitmproxy.exceptions import FlowReadException  # type: ignore
    except ImportError as e:
        return (f"mitmproxy 未安装或未注入 sys.path: {e}。"
                "确认 backend/sitecustomize.py 已把 vendor 加入 sys.path。")

    summaries: list[str] = []
    try:
        with open(flow_file, "rb") as f:
            reader = FlowReader(f)
            for i, flow in enumerate(reader.stream()):
                if i >= max_items:
                    break
                url = flow.request.pretty_url
                if filter and filter.lower() not in url.lower():
                    continue
                summaries.append(_summarize_flow(flow))
    except FlowReadException as e:
        return (f"读取 flow 失败（可能仍在录制中，建议先 stop_traffic_capture）: {e}")
    except Exception as e:  # noqa: BLE001
        return f"读取 flow 错误: {e}"

    if not summaries:
        return "尚无捕获流量或被过滤掉。"
    return "\n---\n".join(summaries)


def stop_traffic_capture() -> str:
    """主动停止监听并清理临时 flow 文件。

    停止后 flow 文件会被删除，请在停止前调用 get_captured_traffic 读取流量。
    """
    with _lock:
        proc = _session.get("process")
        flow_file = _session.get("flow_file", "")
        if proc is None and not flow_file:
            return "无监听进行中。"
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:  # noqa: BLE001
                proc.kill()
        # 清理临时 flow 文件，防磁盘泄漏
        if flow_file:
            try:
                os.unlink(flow_file)
            except Exception:  # noqa: BLE001 文件可能已被删或被占用
                pass
        _session["process"] = None
        _session["flow_file"] = ""
        return f"已停止监听，已清理 flow 文件: {flow_file}"


def _summarize_flow(flow) -> str:
    """单条 flow 摘要：聚焦 AI2 关心的隐形参数（cookie/token/状态校验位等）。"""
    req = flow.request
    resp = flow.response
    method = req.method
    url = req.pretty_url
    status = resp.status_code if resp is not None else "无响应"
    # 关键 headers（聚焦隐形参数：Authorization/Cookie/X-Token/状态校验位等）
    key_headers: dict[str, str] = {}
    for h in ("Authorization", "Cookie", "X-Token", "X-CSRF-Token",
              "X-Auth-Token", "Referer", "Origin", "X-Request-Id"):
        v = req.headers.get(h)
        if v:
            key_headers[h] = v[:200]
    # body 片段（GET 通常无 body，POST/form/json 才有）
    body = ""
    try:
        raw = req.get_text(strict=False) or ""
        body = raw[:500] if raw else ""
    except Exception:  # noqa: BLE001
        body = ""
    return (f"{method} {url} -> {status}\n"
            f"  headers: {key_headers}\n"
            f"  body: {body}")
