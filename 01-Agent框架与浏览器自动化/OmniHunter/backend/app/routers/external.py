"""外接工具与持续挖掘路由。

- 外接工具集成：上传 PowerDesigner(.pdm)/PowerBuilder(.sr*)/.sql/.env 等
  专业工具产物，确定性解析后入 Intel 情报库，供引擎与攻击流水线复用
- POC 扩展：已知 POC 生成确定性变体并复验，命中产出确认漏洞，
  泄露响应继续提取子目标（持续挖掘闭环）
"""
import ipaddress
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..config import get_settings
from ..database import get_db
from ..engine import poc_expand
from ..models import Intel, Task, Vuln
from ..schemas import PocExpandIn, StandardResponse
from ..tools import external_tools
from .tasks import _validate_target_url

router = APIRouter(tags=["external"],
                   dependencies=[Depends(verify_token)])

# 上传大小限制（10MB）
_MAX_UPLOAD = 10 * 1024 * 1024

# host 检索键白名单：域名标签 / IPv4 / IPv6（防脏数据污染情报库检索）
_RE_HOST_LABEL = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9_-]{0,61}[A-Za-z0-9])?$")


def _valid_host_key(host: str) -> bool:
    if not host or len(host) > 253:
        return False
    try:
        ipaddress.ip_address(host)  # 严格校验 IPv4/IPv6
        return True
    except ValueError:
        pass
    return all(_RE_HOST_LABEL.match(p) for p in host.split("."))


@router.post("/external/upload", response_model=StandardResponse)
async def external_upload(file: UploadFile = File(...),
                          host: str = Form(""),
                          db: Session = Depends(get_db)):
    """上传外接工具产物并解析入库（PowerDesigner/PowerBuilder/SQL/配置文件）。

    host 提供时作为情报检索键（引擎按 host 关联消费），留空用文件名。
    """
    filename = file.filename or "upload.bin"
    if not external_tools.is_supported(filename):
        return StandardResponse(
            success=False,
            message=f"不支持的文件类型，支持: "
                    f"{', '.join(sorted(external_tools.SUPPORTED_SUFFIXES))}")
    host = (host or "").strip()
    if host and not _valid_host_key(host):
        return StandardResponse(
            success=False,
            message="host 格式非法（仅允许域名或 IP，作为情报检索键）")
    content_bytes = await file.read()
    if len(content_bytes) > _MAX_UPLOAD:
        return StandardResponse(success=False, message="文件超过 10MB 限制")
    try:
        content = content_bytes.decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return StandardResponse(success=False, message=f"文件读取失败: {e}")

    parsed = external_tools.parse_external(filename, content)
    key = (host or "").strip() or filename
    for item in parsed.get("intel_items", []):
        db.add(Intel(kind=parsed["kind"], key=key, value=item["value"],
                     confidence=item.get("confidence", 0.5),
                     source=f"external:{filename}"))
    db.commit()
    return StandardResponse(
        success=True,
        message=f"{Path(filename).name}: {parsed.get('summary', '解析完成')}"
                f"（情报类型 {parsed['kind']}，已入库）",
        data={"kind": parsed["kind"], "summary": parsed.get("summary", ""),
              "host": key,
              "detail": {k: v for k, v in parsed.items()
                         if k not in ("intel_items", "kind", "summary")}},
    )


@router.post("/poc-expand", response_model=StandardResponse)
async def poc_expand_route(payload: PocExpandIn, db: Session = Depends(get_db)):
    """POC 扩展分析：变体生成 → 确定性复验 → 确认漏洞入库 + 子目标提取。"""
    settings = get_settings()
    # 外部 URL 统一校验（防 SSRF，与任务创建同源）
    _validate_target_url(payload.target_url)

    # POC 内嵌 URL 同样过 SSRF 校验，且必须与目标同 host：
    # 变体全部派生自 poc.url，泄露子目标的同域过滤也锚定 poc.url，
    # host 不一致时校验与过滤整体失效，因此跨 host 直接拒绝
    poc_spec = poc_expand.parse_poc(payload.poc_text)
    if not poc_spec:
        return StandardResponse(
            success=False,
            message="未能从 POC 描述中解析出 URL（需包含 http(s):// 或 curl 命令）")
    _validate_target_url(poc_spec.url)
    poc_host = (urlparse(poc_spec.url).hostname or "").lower()
    tgt_host = (urlparse(payload.target_url).hostname or "").lower()
    if poc_host != tgt_host:
        return StandardResponse(
            success=False,
            message=f"POC URL host（{poc_host}）与目标 host（{tgt_host}）不一致，已拒绝")

    result = await poc_expand.run_poc_expand(
        payload.target_url, payload.poc_text, payload.match_regex)
    if result.get("error"):
        return StandardResponse(success=False, message=result["error"])

    # 确认漏洞入库（提供 task_id 且命中 match 时）
    saved = 0
    if payload.task_id and result.get("confirmed"):
        task = db.get(Task, payload.task_id)
        if task:
            for c in result["confirmed"]:
                db.add(Vuln(
                    task_id=task.id, target_url=payload.target_url,
                    vuln_type="poc_expanded",
                    severity="high",
                    title=f"POC 扩展命中: {c['url']}",
                    detail=f"已知 POC 变体复验命中（{c['note']}），"
                           f"HTTP {c['status']}",
                    payload=payload.poc_text[:2000],
                    evidence=c["snippet"],
                    repro=c["url"], status="pending",
                    confidence=0.9,
                ))
                saved += 1
            db.commit()

    # 子目标持续挖掘提示
    fu = result.get("followups", {})
    extra_msg = ""
    if fu.get("urls"):
        extra_msg = f"；提取子目标 {len(fu['urls'])} 个（可在情报库查看）"
        host = _host_of(payload.target_url)
        for u in fu["urls"][:10]:
            db.add(Intel(kind="leak", key=host,
                         value=u, confidence=0.5,
                         source=f"poc_expand:{int(time.time())}"))
        for c in fu.get("creds", []):
            db.add(Intel(kind="credential", key=c.get("name", "unknown"),
                         value=c.get("masked", ""), confidence=0.6,
                         source="poc_expand"))
        db.commit()

    return StandardResponse(
        success=True,
        message=f"扩展分析完成：变体 {result['variants_total']} 个，"
                f"确认命中 {len(result.get('confirmed', []))} 个，"
                f"入库 {saved} 个{extra_msg}",
        data=result,
    )


def _host_of(url: str) -> str:
    return urlparse(url).netloc or url
