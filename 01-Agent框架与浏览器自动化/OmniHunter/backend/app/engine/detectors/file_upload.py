"""文件上传检测插件 —— 上传端点探测 + 类型校验缺失（有副作用，默认关闭）。"""
from __future__ import annotations

import re
import secrets

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..http_client import get, http_request
from urllib.parse import urljoin, urlparse

# 常见上传端点
_UPLOAD_PATHS = (
    "/upload", "/upload.php", "/file/upload", "/api/upload",
    "/admin/upload", "/user/avatar", "/upload/image", "/api/file",
    "/kindeditor/upload", "/ueditor/index", "/ckeditor/upload",
)

# 无害测试文件：内容为 marker 的 .php.txt 双后缀（不传 webshell，合规探测）
_TEST_CONTENT_TPL = b"<?php echo '%s'; // " + b"a" * 10 + b" ?>\n"

# 上传成功特征
_SUCCESS_SIGS = re.compile(
    r"(\.php|\.jsp|\.asp|\.aspx)\b|uploaded|success|\"url\"|\"path\"",
    re.I)


class FileUploadPlugin(DetectorPlugin):
    id = "upload.type_bypass"
    vuln_type = "file_upload"
    name = "文件上传类型绕过"
    description = "探测上传端点并尝试无害脚本双后缀，检测 MIME/后缀校验缺失"
    default_vector = "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H"
    side_effect_free = False  # 会真实上传无害测试文件，受配置开关控制

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []
        parsed = urlparse(ctx.base_url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        marker = secrets.token_hex(6)

        paths = list(_UPLOAD_PATHS)
        for p in ctx.fp.paths:
            if "upload" in p.lower() or "avatar" in p.lower():
                paths.insert(0, p)

        for path in paths[:8]:
            url = urljoin(root, path)
            # 1) 端点存在性（POST 空体，405/404 视为不存在）
            probe = await http_request("POST", url, data="",
                                       timeout=8, allow_redirects=False)
            if probe.status in (404, 405, 501):
                continue
            # 2) multipart 上传无害测试文件
            content = _TEST_CONTENT_TPL.replace(b"%s", marker.encode())
            fname = f"test_{marker}.php;.txt"  # 分号截断绕过特征
            boundary = "----aififteen" + marker
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; '
                f'filename="{fname}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
            r = await http_request(
                "POST", url,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                data=body, timeout=10, allow_redirects=False)
            if r.status in (200, 201) and r.text and _SUCCESS_SIGS.search(r.text[:8000]):
                # 确认上传后的文件能否访问（若响应给出路径）
                m = re.search(r'["\'](/[\w\-./]+?\.(?:php|jsp|asp|aspx)[^"\']*)["\']',
                              r.text[:8000])
                webshell_url = urljoin(root, m.group(1)) if m else ""
                accessible = False
                if webshell_url:
                    vr = await get(webshell_url, timeout=8)
                    accessible = vr.status == 200 and marker in (vr.text or "")
                findings.append(SuspectFinding(
                    plugin_id=self.id, vuln_type=self.vuln_type,
                    title=f"文件上传校验缺失：{path}",
                    detail=(
                        f"上传端点 {path} 接受了脚本后缀测试文件"
                        f"（{fname}），响应提示上传成功"
                        f"{'，且上传文件可被直接访问执行' if accessible else ''}。"
                        f"测试文件内容为无害 marker 回显，非真实 webshell。"),
                    payload=f"filename={fname}",
                    evidence=(f"上传响应: {r.text[:200]!r}"
                              + (f"; 访问: {webshell_url} {vr.status}" if accessible else "")),
                    url=url,
                    param=webshell_url or url,
                    vector=self.default_vector, confidence=0.7,
                ))
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        if finding.param.startswith("http"):
            r = await get(finding.param, timeout=8)
            if r.status == 200:
                finding.verified = True
                finding.verify_evidence = f"复现: 上传文件仍可访问 ({r.status})"
                finding.confidence = min(0.9, finding.confidence + 0.15)
                return finding
        return None
