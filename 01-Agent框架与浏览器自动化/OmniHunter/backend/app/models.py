"""数据模型。

整合要点：
- Task/Target/Vuln 借鉴 AutoHunter 的挖掘流水线结构；
- Intel 情报沉淀借鉴 agentmemory 的 confidence + lifecycle，可命中复用；
- AgentRun.stage 借鉴 LoopX 的关卡式状态机（recon/scan/exploit/verify/report）；
- AgentMessage 提供 DeerFlow 式 trace，供控制台实时看板。
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from .database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    mode = Column(String, default="EduSRC")  # EduSRC / 企业SRC
    vuln_types = Column(
        Text,
        default="sql_injection,rce,unauthorized_access,idor,file_upload,captcha_bypass,backdoor_compromised",
    )
    source = Column(String, default="manual")  # fofa / manual / both / single
    collect_method = Column(String, default="auto")  # auto / fofa_syntax / nl_intent
    collect_query = Column(Text, default="")
    manual_targets = Column(Text, default="")  # 每行一个 URL
    status = Column(String, default="pending")  # pending/collecting/running/review/done/failed
    error = Column(Text, default="")  # 后台任务异常时回写错误，避免永远卡在 collecting/running
    max_pages = Column(Integer, default=3)
    llm_override = Column(JSON, default=dict)
    fofa_override = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    targets = relationship("Target", back_populates="task", cascade="all,delete")
    vulns = relationship("Vuln", back_populates="task", cascade="all,delete")


class Target(Base):
    __tablename__ = "targets"

    id = Column(String, primary_key=True, default=_uuid)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"))
    url = Column(String, nullable=False)
    host = Column(String, default="")
    ip = Column(String, default="")
    port = Column(Integer, default=0)
    service = Column(String, default="")
    title = Column(String, default="")
    org = Column(String, default="")  # 归属
    score = Column(Float, default=0.0)  # 优先级评分
    alive = Column(Boolean, default=None)
    status = Column(String, default="pending")  # pending/queued/running/done/skipped
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="targets")


class AgentRun(Base):
    """单次 Agent 执行：一个目标一个 Worker 的完整流程。"""
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, default=_uuid)
    target_id = Column(String, ForeignKey("targets.id", ondelete="CASCADE"))
    agent_role = Column(String, nullable=False)  # collector/recon/worker/browser/verifier/reviewer
    status = Column(String, default="pending")  # pending/running/stage_done/done/failed
    stage = Column(String, default="")  # 关卡（LoopX）：recon/scan/exploit/verify/report
    step = Column(Integer, default=0)
    step_budget = Column(Integer, default=40)
    summary = Column(Text, default="")
    error = Column(Text, default="")
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, default=None)


class Vuln(Base):
    __tablename__ = "vulns"

    id = Column(String, primary_key=True, default=_uuid)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"))
    target_id = Column(String, ForeignKey("targets.id", ondelete="CASCADE"))
    target_url = Column(String, default="")
    vuln_type = Column(String, nullable=False)
    severity = Column(String, default="medium")  # info/low/medium/high/critical
    title = Column(String, default="")
    detail = Column(Text, default="")
    payload = Column(Text, default="")
    evidence = Column(Text, default="")
    repro = Column(Text, default="")
    status = Column(String, default="pending")  # pending/ai_reviewed/approved/rejected/submitted
    confidence = Column(Float, default=0.0)  # 借鉴 agentmemory 置信度
    reviewer_note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="vulns")


class Intel(Base):
    """全局情报沉淀（借鉴 agentmemory：confidence + lifecycle + 复用）。

    验证过的凭证/端点/指纹/技术栈 入库，后续 Worker 直接复用。"""
    __tablename__ = "intel"

    id = Column(String, primary_key=True, default=_uuid)
    kind = Column(String, nullable=False)  # credential/endpoint/fingerprint/techstack/leak
    key = Column(String, index=True)  # 检索键，如 host、指纹
    value = Column(Text, default="")
    confidence = Column(Float, default=0.5)  # 置信度 0-1
    hits = Column(Integer, default=0)  # 命中复用次数
    source = Column(String, default="")  # 来源 target/vuln id
    lifecycle = Column(String, default="active")  # active/stale/retired
    tags = Column(JSON, default=list)   # Miner / 用户自定义标签（如 STALE_CANDIDATE）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentMessage(Base):
    """Agent 事件流，供控制台实时看板（借鉴 AutoHunter 事件流 + DeerFlow trace）。"""
    __tablename__ = "agent_messages"

    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("agent_runs.id", ondelete="CASCADE"))
    target_id = Column(String, default="")
    role = Column(String, default="")  # agent role
    level = Column(String, default="info")  # info/think/tool/result/error
    content = Column(Text, default="")
    tool = Column(String, default="")
    tool_args = Column(JSON, default=dict)
    tool_result = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Setting(Base):
    """动态设置：存库，优先级高于 .env（借鉴 AutoHunter 设置页）。"""
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def _default_deadline() -> datetime:
    """定时任务默认期限：1 个月后。"""
    return datetime.utcnow() + timedelta(days=30)


class Schedule(Base):
    """定时任务：周期性启动/关闭扫描，期限默认1月可延长。

    每次触发：按 task_template 生成新 Task 并运行（启动→执行→关闭），
    到达 deadline 后自动停用，前端可一键延长期限。
    """
    __tablename__ = "schedules"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    task_template = Column(JSON, default=dict)  # TaskCreate 配置快照
    cron_expr = Column(String, default="")  # cron 如 "0 2 * * *"；优先于间隔
    interval_minutes = Column(Integer, default=1440)  # 无 cron 时按分钟间隔(默认每日)
    start_at = Column(DateTime, default=datetime.utcnow)
    deadline = Column(DateTime, default=_default_deadline)  # 期限1月，可延长
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime, default=None)
    next_run = Column(DateTime, default=None)
    run_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportTemplate(Base):
    """漏洞报告模板：自定义 markdown/jinja2 模板，按任务生成报告。"""
    __tablename__ = "report_templates"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    content = Column(Text, default="")  # markdown/jinja2 模板
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ====== Spec 2026-08-29: Autonomous Miner ======
# Task.status 新增状态常量（不破坏现有枚举，仅作可读常量）
TASK_PENDING_APPROVAL = "pending_approval"
TASK_REJECTED = "rejected"


class MinerRun(Base):
    """Autonomous Miner 单次运行审计日志（三 loop 计数 + 预算命中）。"""
    __tablename__ = "miner_runs"

    id = Column(String, primary_key=True, default=_uuid)
    trigger_at = Column(DateTime, default=datetime.utcnow)
    loop_coverage_gap_count = Column(Integer, default=0)
    loop_reverify_count = Column(Integer, default=0)
    loop_link_candidate_count = Column(Integer, default=0)
    budget_hit_limit = Column(Boolean, default=False)
    finished_at = Column(DateTime, default=None)
    error_log = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class MinerCandidate(Base):
    """Autonomous Miner Loop3 Link-Extend 候选：新增 Intel 关联域提取结果。

    只入库不触发任何网络调用；用户批准后再转 Intel。"""
    __tablename__ = "miner_candidates"

    id = Column(String, primary_key=True, default=_uuid)
    src_intel_id = Column(String, ForeignKey("intel.id", ondelete="CASCADE"), nullable=False, index=True)
    extracted_kind = Column(String, default="")   # os_fingerprint / passive_dns / cve 等
    extracted_key = Column(String, default="", index=True)   # host / IP / CVE-ID
    status = Column(String, default="pending")   # pending / approved / rejected / skipped
    note = Column(Text, default="")              # out_of_scope 等说明
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ====== Spec 2026-08-30: 自动更新 CVE 库 + 单站协作 ======
class CveEntry(Base):
    """CVE 库条目：NVD + OSV.dev 双源拉取，去重入库。

    存储标准化 CVE 信息，affected 字段携带 vendor/product/versions，
    供 search_by_cve 生成资产测绘平台查询语句，搜索未修复资产。
    """
    __tablename__ = "cve_entries"

    id = Column(String, primary_key=True, default=_uuid)
    cve_id = Column(String, index=True, nullable=False)         # CVE-2024-xxxx
    source = Column(String, default="nvd")                      # nvd / osv
    title = Column(Text, default="")
    description = Column(Text, default="")
    # affected 结构：{"vendor": "...", "product": "...",
    #               "versions": [...], "cpe": [...]}
    affected = Column(JSON, default=dict)
    cvss_score = Column(Float, default=0.0)
    cvss_severity = Column(String, default="")                  # LOW/MEDIUM/HIGH/CRITICAL
    cvss_vector = Column(String, default="")
    published_at = Column(DateTime, default=None)
    updated_at_src = Column(DateTime, default=None)             # 源站更新时间
    references = Column(JSON, default=list)                     # 参考链接
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CveAssetHit(Base):
    """CVE 资产命中：根据 CVE affected 通过资产平台搜出的未修复资产。

    用于「CVE → 搜资产 → 挖掘」流水线，记录搜到的资产和挖掘状态。
    """
    __tablename__ = "cve_asset_hits"

    id = Column(String, primary_key=True, default=_uuid)
    cve_id = Column(String, index=True, nullable=False)         # 关联 CVE
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), default="")
    url = Column(String, default="")                            # 命中资产 URL
    host = Column(String, default="")
    port = Column(Integer, default=0)
    title = Column(String, default="")
    platform = Column(String, default="")                      # fofa / shodan ...
    query = Column(Text, default="")                             # 命中查询语句
    scan_status = Column(String, default="pending")             # pending/scanning/done/failed/skipped
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
