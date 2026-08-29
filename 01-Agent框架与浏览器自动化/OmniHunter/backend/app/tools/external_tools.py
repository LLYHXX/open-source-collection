"""外接专业工具集成：PowerDesigner / PowerBuilder / 通用敏感文件。

与专业开发工具的联动方式（工具为主，确定性解析，零 LLM）：
- PowerDesigner (.pdm)：XML 数据模型 → 解析库表/字段/类型/注释
  → 产出 Intel(kind=db_schema)，供 SQL 注入利用（盲注表名/列名）、
  IDOR 参数定位、敏感字段（password/token/身份证）识别直接消费
- PowerBuilder (.srd/.srw/.srf/.srs/.sra/.srp 导出源码)：静态审计嵌入 SQL
  → 字符串拼接变量、动态 SQL（EXECUTE IMMEDIATE）等注入 sink
  → 产出 Intel(kind=pb_audit)，指导 sqli 插件优先测试对应参数
- 通用敏感文件：.sql（建表语句 schema）、.env/.pem/.key（凭据）
  → Intel(kind=db_schema / credential)

所有解析为纯确定性实现；解析结果统一转 Intel 情报条目入库，
供引擎检测插件与攻击探测流水线按 host 复用。
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

try:  # 带配额的安全 XML 解析器（backend/vendor 注入；缺失时降级为预检 + 标准解析）
    from defusedxml import ElementTree as _SafeET
except ImportError:  # pragma: no cover
    _SafeET = None

# 敏感字段关键词（命中即标记）
SENSITIVE_KEYWORDS = (
    "password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
    "secret_key", "access_key", "private_key", "id_card", "idcard", "sfz",
    "mobile", "phone", "email", "salt", "session", "cookie", "auth",
)

PB_SUFFIXES = {".srd", ".srw", ".srf", ".srs", ".sra", ".srp", ".sru", ".srj"}
SUPPORTED_SUFFIXES = {".pdm", ".sql"} | PB_SUFFIXES | \
    {".env", ".ini", ".conf", ".config", ".pem", ".key"}


def is_supported(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_SUFFIXES


def parse_external(filename: str, content: str) -> dict:
    """按文件类型分发解析。返回 {kind, summary, intel_items}。

    kind: db_schema / pb_audit / credential
    intel_items: [{key, value(json str), confidence}]
    """
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdm":
        return _parse_pdm(filename, content)
    if suffix in PB_SUFFIXES:
        return _parse_pb(filename, content)
    if suffix == ".sql":
        return _parse_sql(filename, content)
    if suffix in (".pem", ".key"):
        return _parse_keyfile(filename, content)
    # .env/.ini/.conf/.config
    return _parse_config(filename, content)


# ===== PowerDesigner (.pdm) =====

def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _parse_pdm(filename: str, content: str) -> dict:
    """解析 PowerDesigner 物理数据模型（XML）：表/列/类型/注释。"""
    # 防 XML 实体炸弹（billion laughs / quadratic blowup）：第一道防线——
    # PDM 为纯 XML 正常不含 DTD，含 DOCTYPE/ENTITY 声明的输入一律拒绝；
    # 第二道防线——优先用 defusedxml（禁止实体/DTD 且带配额）解析
    if re.search(r"<!\s*(DOCTYPE|ENTITY)", content[:65536], re.IGNORECASE):
        return {"kind": "db_schema",
                "summary": "PDM 解析拒绝：文件包含 DTD/ENTITY 声明（潜在实体炸弹）",
                "intel_items": []}
    try:
        if _SafeET is not None:
            root = _SafeET.fromstring(content.encode("utf-8", "replace"))
        else:
            root = ET.fromstring(content.encode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001  ParseError / DefusedXmlException
        return {"kind": "db_schema", "summary": f"PDM 解析失败: {e}",
                "intel_items": []}

    tables = []
    # PDM 结构深，直接按 local-name 找 o:Table 节点
    for tbl in root.iter():
        if _strip_ns(tbl.tag) != "Table":
            continue
        info = {"name": "", "code": "", "comment": "", "columns": []}
        sensitive = []
        for child in tbl:
            t = _strip_ns(child.tag)
            if t == "Name" and not info["name"]:
                info["name"] = (child.text or "").strip()
            elif t == "Code" and not info["code"]:
                info["code"] = (child.text or "").strip()
            elif t == "Comment" and not info["comment"]:
                info["comment"] = (child.text or "").strip()
            elif t == "Columns":
                for col in child:
                    if _strip_ns(col.tag) != "Column":
                        continue
                    c = {"name": "", "code": "", "data_type": "", "comment": ""}
                    for cc in col:
                        ct = _strip_ns(cc.tag)
                        if ct == "Name" and not c["name"]:
                            c["name"] = (cc.text or "").strip()
                        elif ct == "Code" and not c["code"]:
                            c["code"] = (cc.text or "").strip()
                        elif ct == "DataType" and not c["data_type"]:
                            c["data_type"] = (cc.text or "").strip()
                        elif ct == "Comment" and not c["comment"]:
                            c["comment"] = (cc.text or "").strip()
                    info["columns"].append(c)
                    if _is_sensitive(c["code"] + " " + c["name"]):
                        sensitive.append(c["code"] or c["name"])
        if info["code"] or info["name"]:
            info["sensitive_columns"] = sensitive
            tables.append(info)

    summary = (f"PowerDesigner 模型解析成功：{len(tables)} 张表，"
               f"敏感字段 {sum(len(t['sensitive_columns']) for t in tables)} 个")
    items = [{
        "key": filename,
        "value": json.dumps({"source": "powerdesigner", "file": filename,
                             "tables": tables}, ensure_ascii=False),
        "confidence": 0.95,
    }]
    return {"kind": "db_schema", "summary": summary, "intel_items": items,
            "tables": tables}


def _is_sensitive(text: str) -> bool:
    low = (text or "").lower()
    return any(k in low for k in SENSITIVE_KEYWORDS)


# ===== PowerBuilder (.sr*) =====

_SQL_JOIN_RE = re.compile(
    r"(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b[^;\"]*?"
    r"(?:WHERE|SET|VALUES)\b[^;\"]*?\"\s*\+\s*(\w+)", re.IGNORECASE | re.DOTALL)
_SQL_EXEC_RE = re.compile(r"EXECUTE\s+IMMEDIATE\s*:\s*(\w+)", re.IGNORECASE)
_SQL_RETRIEVE_RE = re.compile(r'retrieve\s*=\s*"([^"]+)"', re.IGNORECASE)


def _parse_pb(filename: str, content: str) -> dict:
    """静态审计 PowerBuilder 导出源码：拼接 SQL / 动态 SQL / datawindow retrieve。"""
    sinks: list[dict] = []
    lines = content.splitlines()

    # 1) 字符串拼接 SQL（WHERE/SET/VALUES 后接 + 变量）
    for m in _SQL_JOIN_RE.finditer(content):
        line_no = content[: m.start()].count("\n") + 1
        snippet = "\n".join(lines[max(0, line_no - 2): line_no + 1]).strip()[:300]
        sinks.append({"file": filename, "line": line_no, "type": "sql_concat",
                      "var": m.group(2), "stmt": m.group(1).upper(),
                      "snippet": snippet,
                      "reason": f"SQL 语句拼接变量 {m.group(2)}，存在注入风险"})

    # 2) 动态 SQL EXECUTE IMMEDIATE :var
    for m in _SQL_EXEC_RE.finditer(content):
        line_no = content[: m.start()].count("\n") + 1
        snippet = lines[line_no - 1].strip()[:300] if line_no <= len(lines) else ""
        sinks.append({"file": filename, "line": line_no, "type": "dynamic_sql",
                      "var": m.group(1), "stmt": "EXECUTE IMMEDIATE",
                      "snippet": snippet,
                      "reason": f"动态 SQL 直接执行变量 {m.group(1)}，存在注入风险"})

    # 3) datawindow retrieve SQL（提供参数上下文，供 sqli 插件消费）
    retrieves = []
    for m in _SQL_RETRIEVE_RE.finditer(content):
        sql = m.group(1)
        line_no = content[: m.start()].count("\n") + 1
        retrieves.append({"file": filename, "line": line_no, "sql": sql[:500],
                          "has_arguments": ":arg" in sql.lower() or "?" in sql})

    summary = (f"PowerBuilder 审计完成：拼接/动态 SQL sink {len(sinks)} 个，"
               f"datawindow retrieve {len(retrieves)} 条")
    items = [{
        "key": filename,
        "value": json.dumps({"source": "powerbuilder", "file": filename,
                             "sinks": sinks, "retrieves": retrieves},
                            ensure_ascii=False),
        "confidence": 0.85,
    }]
    return {"kind": "pb_audit", "summary": summary, "intel_items": items,
            "sinks": sinks}


# ===== .sql 建表脚本 =====

_CREATE_RE = re.compile(
    r"CREATE\s+TABLE\s+[`\[\"]*(\w+)[`\]\"]*\s*\((.*?)\)\s*[;S]", re.IGNORECASE | re.DOTALL)
_COLUMN_RE = re.compile(r"[`\[\"]*(\w+)[`\]\"]*\s+([A-Za-z]+(?:\s*\(\d+\))?)")


def _parse_sql(filename: str, content: str) -> dict:
    """解析建表脚本：提取表名/字段/类型/敏感字段。"""
    tables = []
    for m in _CREATE_RE.finditer(content):
        tname, body = m.group(1), m.group(2)
        cols, sensitive = [], []
        for ln in body.splitlines():
            cm = _COLUMN_RE.match(ln.strip())
            if not cm:
                continue
            cname, ctype = cm.group(1), cm.group(2)
            if cname.upper() in ("PRIMARY", "KEY", "UNIQUE", "CONSTRAINT",
                                 "FOREIGN", "INDEX"):
                continue
            cols.append({"code": cname, "data_type": ctype})
            if _is_sensitive(cname):
                sensitive.append(cname)
        tables.append({"name": tname, "code": tname, "comment": "",
                       "columns": cols, "sensitive_columns": sensitive})
    summary = f"SQL 脚本解析成功：{len(tables)} 张表"
    items = [{
        "key": filename,
        "value": json.dumps({"source": "sql_script", "file": filename,
                             "tables": tables}, ensure_ascii=False),
        "confidence": 0.9,
    }]
    return {"kind": "db_schema", "summary": summary, "intel_items": items,
            "tables": tables}


# ===== 凭据类文件 =====

_ASSIGN_RE = re.compile(r"^([A-Za-z_][\w.\-]*)\s*[=:]\s*(.{1,300})$", re.MULTILINE)


def _parse_config(filename: str, content: str) -> dict:
    """解析 .env/.ini/.conf：提取疑似凭据（DB_PASS/AK/SK/TOKEN 等）。"""
    creds = []
    for m in _ASSIGN_RE.finditer(content):
        k, v = m.group(1), m.group(2).strip().strip('"\'')
        if not v:
            continue
        if _is_sensitive(k):
            # 脱敏保留首尾
            masked = v[:4] + "***" + v[-2:] if len(v) > 8 else "***"
            creds.append({"key_name": k, "masked": masked, "file": filename})
    kind = "credential" if creds else "techstack"
    summary = (f"提取疑似凭据 {len(creds)} 条"
               if creds else "未发现凭据类配置")
    items = [{
        "key": filename,
        "value": json.dumps({"source": "config_file", "file": filename,
                             "credentials": creds}, ensure_ascii=False),
        "confidence": 0.8 if creds else 0.4,
    }] if creds else []
    return {"kind": kind, "summary": summary, "intel_items": items,
            "credentials": creds}


def _parse_keyfile(filename: str, content: str) -> dict:
    is_private = "PRIVATE KEY" in content
    items = [{
        "key": filename,
        "value": json.dumps({"source": "key_file", "file": filename,
                             "type": "private_key" if is_private else "key_material"},
                            ensure_ascii=False),
        "confidence": 0.95,
    }]
    return {"kind": "credential", "summary": "发现密钥文件", "intel_items": items}
