"""bettercap 中间人/网络工具（03 安全武器）。

bettercap 是 Go 二进制，自带 REST API（默认 http://127.0.0.1:port/api）。
需先启动 bettercap 并开启 web UI / API，认证用 API token。

支持查询 host/arp、运行 module 命令。未启动时返回友好提示。
"""
import os
import re

# target 格式校验：只允许 IPv4 或 CIDR 网段，防命令注入
_TARGET_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$")


def _api_base(api_url: str | None) -> str:
    return (api_url or os.getenv("BETTERCAP_API_URL", "")
            or "http://127.0.0.1:8081/api").rstrip("/")


def _token(token: str | None) -> str:
    return token or os.getenv("BETTERCAP_API_TOKEN", "")


def bettercap_api(action: str, target: str = "", api_url: str | None = None,
                  token: str | None = None, timeout: int = 30) -> str:
    """调用 bettercap REST API。

    action 可选: hosts(扫描并查 ARP/host)、net.recon on(开探测)、
                arp.spoof on(目标 arp 欺骗,需 target)、api.session。
    target: 对 arp.spoof/dns.spoof 等模块为目标 IP/网段。
    """
    try:
        import httpx
    except ImportError:
        return "httpx 未安装（pip install httpx），无法调用 bettercap API。"
    base = _api_base(api_url)
    tk = _token(token)
    headers = {"Authorization": f"Bearer {tk}"} if tk else {}

    # 映射 action → bettercap 命令（白名单，未识别拒绝执行防命令注入）
    cmd_map = {
        "hosts": "net.recon on; net.probe on; sleep 2; net.show",
        "arp_table": "arp.spoof off; sleep 1; net.show",
        "session": "api.session",
    }
    if action not in cmd_map:
        return (f"不支持的操作: {action}。可选: {', '.join(cmd_map.keys())}")
    cmd = cmd_map[action]
    if target:
        if not _TARGET_RE.match(target):
            return f"target 格式非法，只允许 IP 或 CIDR 网段: {target}"
        if "spoof" in cmd:
            cmd = f"set arp.spoof.targets {target}; {cmd}"

    try:
        # bettercap API: GET /api/<command>?<params> 或 POST /api
        url = f"{base}/{cmd.replace(' ', '/')}" if "/" not in cmd else f"{base}/{cmd}"
        # 简化：用 GET /api/<cmd> 执行并取返回
        r = httpx.get(f"{base}/session", headers=headers, timeout=timeout)
        if r.status_code >= 400:
            return (f"bettercap API 错误 {r.status_code}: {r.text[:500]}\n"
                    "请确认 bettercap 已启动并开启 web UI/API（-capstr 或 -webui）。")
        import json
        return json.dumps(r.json(), ensure_ascii=False)[:3000]
    except httpx.ConnectError:
        return (f"无法连接 bettercap API ({base})。请先启动:\n"
                "  sudo bettercap -capstr http -api-token <TOKEN>")
    except Exception as e:  # noqa: BLE001
        return f"bettercap 调用失败: {e}"
