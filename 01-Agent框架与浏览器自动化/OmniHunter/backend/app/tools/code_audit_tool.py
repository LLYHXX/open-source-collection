"""白盒代码审计工具（纯 Python 内置，借鉴 03/逆向工程/reverse-skill 的 SKILL.md）。

不依赖外部 binary（Semgrep/Pysa 都需 binary），全部用纯 python 库：
  - bandit : Python AST 静态扫描（B1xx 系列插件，硬编码密钥/命令注入/SQL 拼接等）
  - dlint  : Python 危险调用 lint（基于 flake8，扫 eval/exec/pickle.load 等）

库装到 vendor 目录，启动时由 sitecustomize.py 注入 sys.path。
未装时返回友好提示而非崩溃，风格对齐 httpx_tool.py。

白盒模式（white-box）：扫目标源码目录/单文件，输出漏洞清单。
黑盒模式（black-box）：扫运行中的 Web 服务（httpx_probe/nuclei_scan/sqlmap），
                       本工具不参与黑盒，黑盒走 run_traffic_pipeline / run_task。
"""
import os
import subprocess
import sys
from pathlib import Path

# 敏感系统目录黑名单（防路径穿越到系统关键路径）
_SENSITIVE_PATH_PARTS = {"etc", "proc", "sys", "dev", "boot", "windows", "system32"}


def _is_sensitive_path(target_path: str) -> bool:
    """检查路径是否指向系统敏感目录。"""
    try:
        parts_lower = {part.lower() for part in Path(target_path).resolve().parts}
        return bool(parts_lower & _SENSITIVE_PATH_PARTS)
    except Exception:  # noqa: BLE001
        return False


def bandit_scan(target_path: str, severity: str = "low",
                confidence: str = "low", recursive: bool = True) -> str:
    """Bandit 静态扫描 Python 源码找漏洞。

    severity   : low/medium/high（只报 >= 该等级）
    confidence : low/medium/high（只报 >= 该置信度）
    recursive  : True 递归扫目录，False 只扫单文件
    返回告警清单字符串（每条含 id/severity/confidence/file/line/msg/cwe）。
    """
    if not target_path:
        return "请提供要扫描的源码路径（目录或 .py 文件）。"
    if not os.path.exists(target_path):
        return f"路径不存在: {target_path}"
    if _is_sensitive_path(target_path):
        return f"路径指向系统敏感目录，拒绝扫描: {target_path}"

    try:
        from bandit.core import manager as b_manager  # type: ignore
        from bandit.core import config as b_config  # type: ignore
    except ImportError:
        return ("bandit 未安装或未注入 sys.path。"
                "安装: python -m pip install --target=vendor bandit，"
                "并确认 backend/sitecustomize.py 已把 vendor 加入 sys.path。")

    # 等级映射与排序（用于 >= 比较）
    rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    sev_filter = rank.get(severity.upper(), 0)
    conf_filter = rank.get(confidence.upper(), 0)

    try:
        # Bandit 1.9 签名: (config, agg_type, debug, verbose, quiet, profile, ignore_nosec)
        # agg_type='file' 按文件聚合结果；config 用空 BanditConfig（带默认 profile）
        try:
            conf = b_config.BanditConfig()
        except Exception:  # noqa: BLE001
            conf = b_config.BanditConfig(None)
        bmg = b_manager.BanditManager(conf, "file", verbose=False, quiet=True)
        # discover_files(targets, recursive=True)
        bmg.discover_files([target_path], recursive=recursive)
        if not bmg.b_ma:
            return f"未发现可扫描的 .py 文件（路径: {target_path}）。"
        bmg.run_tests()
    except Exception as e:  # noqa: BLE001
        return f"Bandit 扫描异常: {e}"

    # BanditManager 1.9 把结果存在 bmg.results_store，用 get_issue_list() 取
    issues_raw = []
    try:
        store = bmg.get_issue_list()
        issues_raw = list(store)
    except Exception:  # noqa: BLE001
        try:
            # 兜底：从 results_store 取
            rs = getattr(bmg, "results_store", None)
            if rs is not None:
                issues_raw = list(rs.get_issue_list())
        except Exception:  # noqa: BLE001
            issues_raw = []

    out: list[dict] = []
    for issue in issues_raw:
        # issue 是 Issue namedtuple，字段: severity/confidence/fname/lineno/issue_text/test_id/cwe
        sev_str = str(getattr(issue, "severity", "LOW")).upper()
        conf_str = str(getattr(issue, "confidence", "LOW")).upper()
        if rank.get(sev_str, 0) < sev_filter:
            continue
        if rank.get(conf_str, 0) < conf_filter:
            continue
        cwe_obj = getattr(issue, "cwe", None)
        cwe_link = ""
        if cwe_obj is not None:
            cwe_link = getattr(cwe_obj, "link", "") or str(cwe_obj)
        out.append({
            "id": getattr(issue, "test_id", ""),
            "severity": sev_str,
            "confidence": conf_str,
            "file": getattr(issue, "fname", ""),
            "line": getattr(issue, "lineno", 0),
            "msg": getattr(issue, "issue_text", ""),
            "cwe": cwe_link,
        })

    if not out:
        return (f"== bandit_scan {target_path} 扫描完毕，"
                f"无 >= {severity}/{confidence} 等级告警 ==")
    lines = [f"== bandit_scan {target_path} 告警 {len(out)} 条 "
             f"(sev>={severity} conf>={confidence}) =="]
    for it in out:
        mark = " <==" if it["severity"] == "HIGH" else ""
        lines.append(f"  [{it['severity']:6}/{it['confidence']:6}] {it['id']} "
                     f"{it['file']}:{it['line']}{mark}")
        lines.append(f"          {it['msg']}")
        if it["cwe"]:
            lines.append(f"          CWE: {it['cwe']}")
    return "\n".join(lines)


def dlint_scan(target_path: str, recursive: bool = True) -> str:
    """Dlint 扫 Python 危险调用（eval/exec/pickle/system 等）。

    走 `python -m flake8` + dlint 插件（DUO 系列），输出违反规则代码点。
    """
    if not target_path:
        return "请提供要扫描的源码路径。"
    if not os.path.exists(target_path):
        return f"路径不存在: {target_path}"
    if _is_sensitive_path(target_path):
        return f"路径指向系统敏感目录，拒绝扫描: {target_path}"

    # 用 `python -m flake8` 调用（vendor 装的 flake8 是 Python 模块，无 exe）
    args = [sys.executable, "-m", "flake8",
            "--select=DUO",
            "--extend-ignore=E,W,F,C",
            "--show-source",
            target_path]
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        out_text = (r.stdout or r.stderr or "").strip()
        # flake8 找不到 dlint 插件时 stdout 可能为空，stderr 有提示
        if not out_text and r.returncode not in (0, 1):
            return (f"flake8/dlint 调用失败（exit={r.returncode}）。"
                    f"确认 dlint 已装 vendor 且 backend/sitecustomize.py 已注入。")
    except subprocess.TimeoutExpired:
        return "dlint 扫描超时（120s），目录可能过大。"
    except Exception as e:  # noqa: BLE001
        return f"dlint 扫描错误: {e}"

    if not out_text:
        return f"== dlint_scan {target_path} 无危险调用告警 =="
    lines = [f"== dlint_scan {target_path} 告警如下（DUO=dlint 规则）=="]
    for ln in out_text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        lines.append(f"  {ln}")
    return "\n".join(lines)


def code_audit_summary(target_path: str, severity: str = "low") -> str:
    """一站式白盒审计：bandit + dlint 合并摘要。

    给 CodeAuditor Agent 调用，输出统一格式告警清单 + 严重度统计。
    """
    bandit_out = bandit_scan(target_path, severity=severity,
                             confidence="low", recursive=True)
    dlint_out = dlint_scan(target_path, recursive=True)

    lines = [f"== code_audit_summary {target_path} =="]
    # 统计
    b_high = bandit_out.count("[HIGH")
    b_med = bandit_out.count("[MEDIUM")
    b_low = bandit_out.count("[LOW")
    lines.append(f"bandit: HIGH={b_high} MEDIUM={b_med} LOW={b_low}")
    lines.append("")
    lines.append("--- bandit 报告 ---")
    lines.append(bandit_out)
    lines.append("")
    lines.append("--- dlint 报告 ---")
    lines.append(dlint_out)
    return "\n".join(lines)
