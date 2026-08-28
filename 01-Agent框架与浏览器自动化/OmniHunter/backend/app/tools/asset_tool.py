"""资产侦察工具（纯 Python 内置版，借鉴 03/AI渗透测试Agent/DeepEye）。

不依赖 nmap/subfinder 等外部二进制：
  - subdomain_enum : crt.sh 证书透明度 + dnspython 解析 A 记录
  - port_scan_basic: 纯 socket TCP connect，nmap 未装时的兜底并发扫描

库装到 vendor 目录，启动时由 sitecustomize.py 注入 sys.path。
未装依赖时降级（仅 crt.sh / 不解析 A 记录），不崩溃。
"""
import json
import socket
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def subdomain_enum(domain: str, limit: int = 50) -> str:
    """枚举子域名：crt.sh 证书透明度 + dnspython 解析 A 记录。

    流程（对齐 DeepEye modules/reconnaissance/subdomain_hunter.py）：
      1) 查 crt.sh https://crt.sh/?q=%.{domain}&output=json 拿证书 SAN 子域名
      2) 用 dnspython 解析每个候选子域的 A 记录（未装则只返回证书收集结果）
      3) 去重 + 限 limit 条输出

    domain 传 example.com 形式（不带 www/http）。
    """
    domain = (domain or "").strip().lower()
    if not domain or "/" in domain:
        return "请传根域名（example.com 形式，不带 http:// 与路径）。"
    domain = domain.replace("http://", "").replace("https://", "")
    if domain.startswith("www."):
        domain = domain[4:]
    if "/" in domain:
        domain = domain.split("/")[0]

    # ===== 1. crt.sh 证书透明度 =====
    crt_subs: list[str] = []
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 OmniHunter"})
        # nosec B310 — 仅请求 crt.sh 固定 https URL 取证书透明度数据
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:  # nosec B310
            data = json.loads(r.read().decode("utf-8", errors="ignore"))
        for entry in data:
            nv = entry.get("name_value", "") or ""
            # 一条 name_value 可能含多个域名（换行分隔），含 *. 通配
            for line in nv.split("\n"):
                line = line.strip().lower()
                if not line or "*" in line:
                    continue
                if line.endswith(domain) and line not in crt_subs:
                    crt_subs.append(line)
    except Exception as e:  # noqa: BLE001
        # crt.sh 偶发不可达/限流，降级继续
        crt_subs_err = f"crt.sh 查询失败（{e}），仅靠 DNS 解析候选"

    crt_subs_err = ""  # 上方 except 已用，简化逻辑：无错时为空串
    if not crt_subs:
        # 加常见前缀做 DNS 暴破兜底（crt.sh 失败时尤其有用）
        prefix_list = ("www", "mail", "ftp", "admin", "api", "dev", "test",
                       "stage", "staging", "vpn", "ns1", "ns2", "m", "app",
                       "blog", "shop", "static", "img", "cdn", "portal",
                       "git", "jenkins", "grafana", "kibana", "zabbix")
        crt_subs = [f"{p}.{domain}" for p in prefix_list]

    # ===== 2. dnspython 解析 A 记录 =====
    resolved: list[dict] = []
    try:
        import dns.resolver  # type: ignore
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3
        resolver.lifetime = 5
        has_dns = True
    except ImportError:
        has_dns = False

    seen: set[str] = set()
    for sub in crt_subs[:limit]:
        if sub in seen:
            continue
        seen.add(sub)
        ips: list[str] = []
        if has_dns:
            try:
                answers = resolver.resolve(sub, "A")
                ips = [a.to_text() for a in answers]
            except Exception:  # noqa: BLE001
                ips = []
        else:
            # 兜底用系统 socket.gethostbyname（A 记录解析）
            try:
                ip = socket.gethostbyname(sub)
                ips = [ip]
            except Exception:  # noqa: BLE001
                ips = []
        # 有 IP 才算活子域
        if ips:
            resolved.append({"subdomain": sub, "ips": ips})

    if not resolved:
        msg = f"未解析到活子域（crt.sh 收集 {len(crt_subs)} 个候选，但都无 A 记录）。"
        if not has_dns:
            msg += " dnspython 未装，仅用 socket.gethostbyname 兜底解析。"
        return msg

    lines = [f"== subdomain_enum {domain} resolved={len(resolved)} =="]
    if not has_dns:
        lines.append("(dnspython 未装，仅用 socket 兜底；安装后 A 记录解析更全: "
                     "pip install --target=vendor dnspython)")
    for item in resolved:
        lines.append(f"  {item['subdomain']}  -> {', '.join(item['ips'])}")
    return "\n".join(lines)


def port_scan_basic(host: str, ports: str = "22,80,443,3306,8080,8443",
                   timeout: int = 2, workers: int = 50) -> str:
    """并发 TCP connect 扫描（nmap 未装时的纯 python 兜底）。

    默认扫 22/80/443/3306/8080/8443，timeout 每端口秒，workers 并发。
    开放端口尝试抓 banner（前 256 字节，HTTP/SSH/SMTP 等常见服务）。
    """
    host = (host or "").strip()
    if not host:
        return "请提供 host（域名或 IP）。"
    # 去协议头
    host = host.replace("http://", "").replace("https://", "").split("/")[0]
    if host.startswith("www."):
        # 端口扫描不应去掉 www，但需保证是主机而非 URL
        pass

    # 解析端口
    port_list: list[int] = []
    for p in str(ports).split(","):
        p = p.strip()
        if p.isdigit():
            port_list.append(int(p))
        elif "-" in p:
            try:
                a, b = p.split("-", 1)
                port_list.extend(range(int(a), int(b) + 1))
            except Exception:  # noqa: BLE001
                continue
    if not port_list:
        return f"端口解析失败: ports={ports}"
    port_list = list(dict.fromkeys(port_list))  # 去重保序

    open_ports: list[dict] = []

    def _scan_one(port: int) -> dict | None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                r = s.connect_ex((host, port))
                if r != 0:
                    return None
                banner = ""
                try:
                    # HTTP 端口先发 HTTP 请求拿响应头
                    if port in (80, 8080, 8000, 8888, 8443, 443):
                        s.sendall(b"GET / HTTP/1.0\r\nHost: %s\r\n\r\n" % host.encode())
                    banner = s.recv(256).decode("utf-8", errors="ignore").strip()
                except Exception:  # noqa: BLE001
                    banner = ""
                return {"port": port, "banner": banner[:200]}
        except Exception:  # noqa: BLE001
            return None

    # 并发扫描
    try:
        with ThreadPoolExecutor(max_workers=min(workers, len(port_list))) as ex:
            futures = {ex.submit(_scan_one, p): p for p in port_list}
            for fut in as_completed(futures):
                res = fut.result()
                if res:
                    open_ports.append(res)
    except Exception as e:  # noqa: BLE001
        return f"并发扫描启动失败: {e}"

    if not open_ports:
        return (f"== port_scan_basic {host} scanned={len(port_list)} "
                f"open=0 ==\n全部端口关闭或被过滤。"
                f"（纯 socket TCP connect，建议 nmap 更精准：nmap -sV {host}）")

    open_ports.sort(key=lambda x: x["port"])
    lines = [f"== port_scan_basic {host} scanned={len(port_list)} "
             f"open={len(open_ports)} =="]
    for item in open_ports:
        svc = _guess_service(item["port"], item["banner"])
        ban = f" banner={item['banner']!r}" if item["banner"] else ""
        lines.append(f"  {item['port']:5}/tcp open  {svc}{ban}")
    lines.append("（纯 socket TCP connect 兜底，nmap 未装时用；"
                 "如需服务版本指纹请装 nmap 走 nmap_scan 工具）")
    return "\n".join(lines)


def _guess_service(port: int, banner: str) -> str:
    """根据端口+banner 猜服务名。"""
    bl = banner.lower() if banner else ""
    if "ssh" in bl:
        return "ssh"
    if "http" in bl or "server:" in bl:
        return "http"
    if "smtp" in bl:
        return "smtp"
    if "ftp" in bl or "vsftpd" in bl:
        return "ftp"
    if "mysql" in bl:
        return "mysql"
    if "redis" in bl:
        return "redis"
    # 端口兜底
    well_known = {
        21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
        80: "http", 110: "pop3", 143: "imap", 443: "https",
        445: "smb", 3306: "mysql", 3389: "rdp", 5432: "postgresql",
        5900: "vnc", 6379: "redis", 8080: "http-proxy", 8443: "https-alt",
        27017: "mongodb", 9200: "elasticsearch",
    }
    return well_known.get(port, "unknown")
