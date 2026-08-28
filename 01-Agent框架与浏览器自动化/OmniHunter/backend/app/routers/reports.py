"""漏洞报告模板路由：模板 CRUD + 按任务生成报告。

支持自定义 markdown/jinja2 模板；未装 jinja2 时用简单 {{ var }} 替换兜底。
"""
import re
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import ReportTemplate, Task, Vuln
from ..schemas import (
    ReportGenerate,
    ReportTemplateCreate,
    ReportTemplateOut,
    ReportTemplateUpdate,
    StandardResponse,
)

router = APIRouter(prefix="/reports", tags=["reports"],
                   dependencies=[Depends(verify_token)])

# 内置默认模板：无任何自定义模板时兜底
DEFAULT_TEMPLATE = """# 漏洞报告 - {{ task_name }}

生成时间：{{ generated_at }}
漏洞总数：{{ vuln_count }}

## 严重程度分布
{{ severity_summary }}

## 漏洞清单
{% for v in vulns %}
### {{ loop.index }}. {{ v.title }} [{{ v.severity }}]
- 类型：{{ v.vuln_type }}
- 目标：{{ v.target_url }}
- 状态：{{ v.status }}（置信度 {{ v.confidence }}）
- 详情：{{ v.detail }}
- Payload：{{ v.payload }}
- 证据：{{ v.evidence }}
- 复现：{{ v.repro }}
{% endfor %}
"""

# ===== 主流 SRC 平台预置模板（启动时自动 seed 进数据库）=====
PRESET_TEMPLATES: dict[str, str] = {
    # 补天公益漏洞响应平台（含厂商/POC/修复建议标准字段）
    "补天SRC": """# 补天漏洞报告 - {{ task_name }}

## 1. 漏洞标题
{{ vulns[0].title if vulns else '' }}

## 2. 漏洞URL
{{ vulns[0].target_url if vulns else '' }}

## 3. 漏洞类型
{{ vulns[0].vuln_type if vulns else '' }}

## 4. 漏洞等级
{{ vulns[0].severity if vulns else '' }}

## 5. 厂商
（请填写厂商名称）

## 6. 漏洞描述
{{ vulns[0].detail if vulns else '' }}

## 7. 漏洞PoC（请勿对外泄露，避免被恶意利用）
```
{{ vulns[0].payload if vulns else '' }}
```

## 8. 复现步骤
{% for v in vulns %}
{{ loop.index }}. 访问目标：{{ v.target_url }}
{{ v.repro }}
{% endfor %}

## 9. 修复建议
- 升级到最新版本
- 对用户输入做严格过滤与白名单校验
- 服务端鉴权校验 + 参数化查询

## 10. 证据截图
（请附上复现截图，含时间戳与目标 URL）

## 11. 报告时间
{{ generated_at }}

## 12. 报告人
（请填写补天昵称）
""",
    # EDUSRC 教育行业漏洞报告（含教育资产/影响范围）
    "EDUSRC": """# EDUSRC 教育行业漏洞报告 - {{ task_name }}

## 一、漏洞信息
- 漏洞标题：{{ vulns[0].title if vulns else '' }}
- 漏洞URL：{{ vulns[0].target_url if vulns else '' }}
- 漏洞类型：{{ vulns[0].vuln_type if vulns else '' }}
- 漏洞等级：{{ vulns[0].severity if vulns else '' }}

## 二、教育资产信息
- 学校/单位：（请填写）
- 资产域名/IP：
- 资产归属：教育行业

## 三、漏洞描述
{{ vulns[0].detail if vulns else '' }}

## 四、漏洞PoC
```
{{ vulns[0].payload if vulns else '' }}
```

## 五、复现步骤
{% for v in vulns %}
{{ loop.index }}. {{ v.target_url }}
   - 操作：{{ v.repro }}
   - 预期：{{ v.detail }}
{% endfor %}

## 六、影响范围
- 影响用户：（如：全校师生/某学院师生）
- 影响数据：（如：学生学籍/成绩/个人信息）
- 影响功能：（如：教务系统/选课系统）

## 七、修复建议
- 输入校验：参数化查询、白名单过滤
- 鉴权加固：服务端校验权限、Session 失效控制
- 日志审计：记录关键操作便于追溯

## 八、报告人信息
- 报告人：（请填写 EDUSRC 昵称）
- 联系方式：（可选）
- 报告时间：{{ generated_at }}
""",
    # 漏洞盒子 SRC 报告（含奖励等级/厂商确认字段）
    "漏洞盒子": """# 漏洞盒子报告 - {{ task_name }}

## 基本信息
| 字段 | 值 |
|------|-----|
| 漏洞标题 | {{ vulns[0].title if vulns else '' }} |
| 漏洞URL | {{ vulns[0].target_url if vulns else '' }} |
| 漏洞类型 | {{ vulns[0].vuln_type if vulns else '' }} |
| 漏洞等级 | {{ vulns[0].severity if vulns else '' }} |
| 奖励等级 | （待厂商确认） |
| 厂商 | （请填写） |
| 报告时间 | {{ generated_at }} |

## 漏洞描述
{{ vulns[0].detail if vulns else '' }}

## PoC（禁止外传）
```
{{ vulns[0].payload if vulns else '' }}
```

## 复现过程
{% for v in vulns %}
### {{ loop.index }}. {{ v.title }}
- URL：{{ v.target_url }}
- 操作：{{ v.repro }}
- 证据：{{ v.evidence }}
{% endfor %}

## 危害说明
- 数据泄露风险：
- 业务影响：
- 提权可能：

## 修复方案
1. 立即修复：
2. 长期方案：
3. 复测建议：

## 报告人
（请填写漏洞盒子账号）
""",
    # CNVD 国家信息安全漏洞共享平台（含 CVE 关联/通用漏洞编号）
    "CNVD": """# CNVD 漏洞报告 - {{ task_name }}

## 一、漏洞基本信息
- 漏洞名称：{{ vulns[0].title if vulns else '' }}
- 漏洞URL/资产：{{ vulns[0].target_url if vulns else '' }}
- 漏洞类型：{{ vulns[0].vuln_type if vulns else '' }}
- 漏洞等级：{{ vulns[0].severity if vulns else '' }}
- CVE 编号：（如有，请填写，便于 CNVD 关联）
- CNVD 编号：（待 CNVD 分配）

## 二、漏洞描述
{{ vulns[0].detail if vulns else '' }}

## 三、漏洞PoC（敏感信息，仅限审核可见）
```
{{ vulns[0].payload if vulns else '' }}
```

## 四、复现步骤
{% for v in vulns %}
{{ loop.index }}. 访问 {{ v.target_url }}
   - 操作：{{ v.repro }}
   - 现象：{{ v.evidence }}
{% endfor %}

## 五、影响范围
- 受影响厂商：
- 受影响产品/版本：
- 受影响资产数量：
- 影响程度：（如：远程代码执行/数据泄露/服务中断）

## 六、修复建议
- 升级方案：
- 临时缓解：

## 七、报告人
- 姓名/昵称：
- 联系方式：（用于 CNVD 协调）
- 报告时间：{{ generated_at }}

## 八、附件
- 复现截图：
- 抓包文件：
""",
    # CNNVD 国家信息安全漏洞库（更偏 CVE 标准化录入）
    "CNNVD": """# CNNVD 漏洞录入报告 - {{ task_name }}

## 1. 漏洞名称
{{ vulns[0].title if vulns else '' }}

## 2. CVE 编号
（如有 CVE 编号请填写，CNNVD 会做 CVE 同步）

## 3. 漏洞类型
{{ vulns[0].vuln_type if vulns else '' }}

## 4. 危害等级
{{ vulns[0].severity if vulns else '' }}

## 5. 受影响产品
- 厂商：
- 产品名称：
- 版本范围：

## 6. 漏洞描述
{{ vulns[0].detail if vulns else '' }}

## 7. 漏洞PoC（敏感，限审核可见）
```
{{ vulns[0].payload if vulns else '' }}
```

## 8. 复现步骤
{% for v in vulns %}
{{ loop.index }}. {{ v.target_url }} — {{ v.repro }}
{% endfor %}

## 9. 修复方案
- 升级到厂商最新版本
- 应用官方补丁

## 10. 报告人
（请填写 CNNVD 账号或联系方式）
报告时间：{{ generated_at }}
""",
    # 企业内部安全自检模板（含修复 SLA/责任人/复测字段）
    "企业自检": """# 企业安全自检报告 - {{ task_name }}

## 报告元数据
| 字段 | 值 |
|------|-----|
| 报告时间 | {{ generated_at }} |
| 漏洞总数 | {{ vuln_count }} |
| 严重程度分布 | {{ severity_summary }} |
| 责任团队 | （请填写业务团队） |
| 安全负责人 | （请填写） |
| 复测截止 | （按 SLA：critical=24h / high=72h / medium=7d） |

## 漏洞清单
{% for v in vulns %}
### {{ loop.index }}. [{{ v.severity }}] {{ v.title }}
- **漏洞类型**：{{ v.vuln_type }}
- **目标**：{{ v.target_url }}
- **当前状态**：{{ v.status }}（置信度 {{ v.confidence }}）
- **风险描述**：{{ v.detail }}
- **复现 Payload**：
  ```
  {{ v.payload }}
  ```
- **证据**：{{ v.evidence }}
- **复现步骤**：{{ v.repro }}
- **修复建议**：
  - 立即修复：
  - 长期加固：
- **SLA 截止**：（{{ v.severity }} 级，待定）
- **复测结果**：□ 已修复  □ 未修复  □ 部分修复
{% endfor %}

## 整改跟踪
- critical：{{ severity_summary }}
- 修复完成率：
- 待复测清单：

## 风险评估
- 整体风险等级：
- 数据泄露可能性：
- 业务影响：

## 报告人
（请填写）
""",
    # 通用模板（精简，适配任何场景，可作二次定制起点）
    "通用": """# 漏洞报告 - {{ task_name }}

生成时间：{{ generated_at }}
漏洞总数：{{ vuln_count }}

## 严重程度分布
{{ severity_summary }}

## 漏洞清单
{% for v in vulns %}
### {{ loop.index }}. {{ v.title }} [{{ v.severity }}]
- 类型：{{ v.vuln_type }}
- 目标：{{ v.target_url }}
- 状态：{{ v.status }}（置信度 {{ v.confidence }}）
- 详情：{{ v.detail }}
- Payload：{{ v.payload }}
- 证据：{{ v.evidence }}
- 复现：{{ v.repro }}
{% endfor %}
""",
}


def seed_preset_templates(db: Session) -> int:
    """启动时把预置 SRC 模板 seed 进数据库（已存在同名则跳过）。

    返回新增数量。在 main.py startup 事件中调用一次。
    """
    added = 0
    for name, content in PRESET_TEMPLATES.items():
        exists = db.scalar(select(ReportTemplate).where(
            ReportTemplate.name == name))
        if exists is not None:
            continue
        # 「通用」标记为默认模板（其它预置为非默认）
        is_default = (name == "通用")
        if is_default:
            # 清掉其它默认
            for o in db.scalars(select(ReportTemplate).where(
                    ReportTemplate.is_default.is_(True))):
                o.is_default = False
        db.add(ReportTemplate(name=name, content=content,
                              is_default=is_default))
        added += 1
    if added:
        db.commit()
    return added


@router.get("/templates", response_model=list[ReportTemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return list(db.scalars(
        select(ReportTemplate).order_by(ReportTemplate.created_at.desc())
    ))


@router.post("/templates", response_model=StandardResponse)
def create_template(payload: ReportTemplateCreate, db: Session = Depends(get_db)):
    t = ReportTemplate(name=payload.name, content=payload.content,
                       is_default=payload.is_default)
    if payload.is_default:
        # 只允许一个默认：清掉其它默认
        for o in db.scalars(select(ReportTemplate).where(
                ReportTemplate.is_default.is_(True))):
            o.is_default = False
    db.add(t)
    db.commit()
    db.refresh(t)
    return StandardResponse(message="模板已创建", data={"id": t.id})


@router.put("/templates/{template_id}", response_model=StandardResponse)
def update_template(template_id: str, payload: ReportTemplateUpdate,
                    db: Session = Depends(get_db)):
    t = db.get(ReportTemplate, template_id)
    if not t:
        raise HTTPException(404, "模板不存在")
    if payload.name is not None:
        t.name = payload.name
    if payload.content is not None:
        t.content = payload.content
    if payload.is_default is not None:
        if payload.is_default:
            for o in db.scalars(select(ReportTemplate).where(
                    ReportTemplate.is_default.is_(True),
                    ReportTemplate.id != template_id)):
                o.is_default = False
        t.is_default = payload.is_default
    db.commit()
    return StandardResponse(message="已更新")


@router.delete("/templates/{template_id}", response_model=StandardResponse)
def delete_template(template_id: str, db: Session = Depends(get_db)):
    t = db.get(ReportTemplate, template_id)
    if not t:
        raise HTTPException(404, "模板不存在")
    db.delete(t)
    db.commit()
    return StandardResponse(message="已删除")


@router.post("/generate", response_model=StandardResponse)
def generate_report(payload: ReportGenerate, db: Session = Depends(get_db)):
    """按模板把任务的漏洞渲染成报告文本。"""
    task = db.get(Task, payload.task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    vulns = list(db.scalars(
        select(Vuln).where(Vuln.task_id == payload.task_id)
    ))

    # 选模板：指定 > 默认 > 内置
    tpl = None
    if payload.template_id:
        tpl = db.get(ReportTemplate, payload.template_id)
    if not tpl:
        tpl = db.scalar(select(ReportTemplate).where(
            ReportTemplate.is_default.is_(True)))
    content = tpl.content if tpl else DEFAULT_TEMPLATE

    data = {
        "task_name": task.name,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "vuln_count": len(vulns),
        "severity_summary": _severity_summary(vulns),
        "vulns": [_vuln_dict(v) for v in vulns],
    }
    report = _render(content, data)
    return StandardResponse(
        message=f"已生成报告（{len(vulns)} 个漏洞）",
        data={"report": report, "template": tpl.name if tpl else "内置默认"},
    )


def _vuln_dict(v: Vuln) -> dict:
    return {
        "vuln_type": v.vuln_type, "severity": v.severity, "title": v.title,
        "target_url": v.target_url, "status": v.status,
        "confidence": round(v.confidence, 2), "detail": v.detail or "",
        "payload": v.payload or "", "evidence": v.evidence or "",
        "repro": v.repro or "",
    }


def _severity_summary(vulns) -> str:
    if not vulns:
        return "无漏洞"
    c = Counter(v.severity for v in vulns)
    return " · ".join(f"{k}:{n}" for k, n in c.items())


def _render(content: str, data: dict) -> str:
    """渲染模板：优先 jinja2，未装则简单 {{ var }} 替换（不支持循环）。"""
    try:
        from jinja2 import Template
        return Template(content).render(**data)
    except ImportError:
        # 兜底：只替换简单变量，循环块原样保留
        def repl(m):
            key = m.group(1).strip()
            val = data.get(key, "")
            return str(val) if not isinstance(val, (list, dict)) else str(val)
        return re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, content)
